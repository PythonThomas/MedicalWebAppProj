import os

import psycopg2
from psycopg2.extras import RealDictCursor

# SQL executed once at startup to prepare the database.
# "IF NOT EXISTS" makes every statement safe to re-run — nothing happens if
# the table or extension is already there.
_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS certificate_requests (
    id               SERIAL PRIMARY KEY,        -- auto-incrementing integer row ID
    user_id          UUID NOT NULL DEFAULT gen_random_uuid(),  -- random UUID, used as the public-facing record ID
    reason_for       VARCHAR(50) NOT NULL,
    other_reason     TEXT,                       -- NULL unless reason_for = 'other'
    surname          VARCHAR(100) NOT NULL,
    given_name       VARCHAR(100) NOT NULL,
    date_of_birth    DATE NOT NULL,
    email            VARCHAR(254) NOT NULL,      -- 254 is the maximum valid email length per RFC 5321
    absence_start    DATE NOT NULL,
    absence_end      DATE NOT NULL,
    paypal_order_id  VARCHAR(100),               -- NULL until payment is captured
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    email       VARCHAR(254) NOT NULL,
    message     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


def get_connection():
    # Read connection details from environment variables set in .env.
    # Defaults are provided so the app starts without crashing if a variable
    # is missing, but a real database will still be needed at runtime.
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "jeffcare"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def init_db():
    # Create tables on startup. Called once from app.py before the first
    # request is handled, so the schema is always in place.
    conn = get_connection()
    try:
        # "with conn:" is psycopg2's transaction context manager — it commits
        # automatically on success and rolls back if an exception is raised.
        with conn:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA)
    finally:
        # Always close the connection, even if an exception occurred above.
        conn.close()


def save_certificate_request(data: dict) -> str:
    # %s placeholders let psycopg2 handle quoting and escaping of each value,
    # which prevents SQL injection regardless of what the values contain.
    sql = """
        INSERT INTO certificate_requests
            (reason_for, other_reason, surname, given_name, date_of_birth,
             email, absence_start, absence_end, paypal_order_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING user_id::text
    """
    # "or None" converts empty strings to NULL so optional fields are stored
    # as proper NULL rather than an empty string in the database.
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    data["reasonFor"],
                    data.get("otherReason") or None,
                    data["surname"],
                    data["givenName"],
                    data["dateOfBirth"],
                    data["email"],
                    data["absenceStartDate"],
                    data["absenceEndDate"],
                    data.get("paypalOrderId") or None,
                ))
                # RETURNING user_id::text tells PostgreSQL to send back the
                # UUID it just generated, cast to a plain string for easy use.
                return cur.fetchone()[0]
    finally:
        conn.close()


def get_certificate_request(user_id: str) -> dict | None:
    sql = """
        SELECT user_id::text, reason_for, other_reason, surname, given_name,
               date_of_birth, email, absence_start, absence_end,
               paypal_order_id, created_at
        FROM certificate_requests
        WHERE user_id = %s::uuid
    """
    conn = get_connection()
    try:
        # RealDictCursor returns each row as a dict {"column": value} instead
        # of a plain tuple, so callers can access fields by name (row["email"])
        # rather than by index (row[6]).
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            # fetchone() returns None if no row matched, so we check before
            # converting to dict.
            return dict(row) if row else None
    finally:
        conn.close()


def save_contact_message(data: dict) -> None:
    sql = """
        INSERT INTO contact_messages (name, email, message)
        VALUES (%s, %s, %s)
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (data["name"], data["email"], data["message"]))
    finally:
        conn.close()
