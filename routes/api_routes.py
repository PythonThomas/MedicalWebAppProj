"""API routes blueprint

This blueprint contains JSON API endpoints consumed by the frontend. It is
registered in the main application under the `/api` URL prefix (so the final
endpoints are `/api/hello`, `/api/data`, `/api/paypal/create-order`, and
`/api/paypal/capture-order`).
"""

import html
import os
import re
from base64 import b64encode
from datetime import datetime

import requests as http
from flask import Blueprint, jsonify, request

api_routes = Blueprint("api_routes", __name__)

# PayPal API base URL — defaults to sandbox; set PAYPAL_BASE_URL in .env for production
PAYPAL_BASE = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

# Fixed certificate processing fee charged at payment step
CERT_PRICE_AUD = "12.99"

# Allow-lists for fields that must match a fixed set of values
_ALLOWED_REASONS = {"sick_leave", "carers_leave", "other"}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}$")


# ============================================
# SECURITY HELPERS
# ============================================
# These helpers exist specifically to prevent SQL injection and XSS/JS injection.
# All user-supplied values must pass through them before being used or stored.

def _sanitize(value, max_length=500):
    """Escape HTML special characters and truncate to max_length.

    Converts < > & " ' into their HTML entities so any embedded script tags
    or SQL fragments are rendered harmless if the value is ever written into
    an HTML page or interpolated into a query string.
    """
    if not isinstance(value, str):
        return ""
    return html.escape(value.strip())[:max_length]


def _valid_date(value):
    """Return True only for a non-empty, well-formed YYYY-MM-DD date string."""
    if not isinstance(value, str) or not _DATE_RE.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _valid_email(value):
    """Return True if value has the basic shape of an email address."""
    return isinstance(value, str) and bool(_EMAIL_RE.match(value.strip()))


# ============================================
# PAYPAL HELPERS
# ============================================

def _paypal_token():
    """Exchange client credentials for a short-lived PayPal access token."""
    client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    secret = os.getenv("PAYPAL_CLIENT_SECRET", "")
    creds = b64encode(f"{client_id}:{secret}".encode()).decode()
    resp = http.post(
        f"{PAYPAL_BASE}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data="grant_type=client_credentials",
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ============================================
# API ENDPOINTS
# ============================================

@api_routes.route("/hello", methods=["GET"])
def hello():
    """Return a simple greeting message as JSON."""
    return jsonify({"message": "Hello from Python backend!"})


@api_routes.route("/paypal/create-order", methods=["POST"])
def paypal_create_order():
    """Create a PayPal order for the certificate processing fee (12.99 AUD).

    Called by the frontend PayPal SDK's createOrder callback. Returns the
    PayPal-assigned order ID which the SDK uses to launch the payment overlay.
    """
    try:
        token = _paypal_token()
        resp = http.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {"currency_code": "AUD", "value": CERT_PRICE_AUD},
                    "description": "JeffCare Medical Certificate Request",
                }],
            },
            timeout=10,
        )
        resp.raise_for_status()
        return jsonify({"id": resp.json()["id"]})
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Could not create PayPal order. Please try again.",
        }), 500


@api_routes.route("/paypal/capture-order", methods=["POST"])
def paypal_capture_order():
    """Capture an approved PayPal order by its order ID.

    Called by the frontend after the user approves payment in the PayPal
    overlay. A successful capture confirms that funds have been collected.
    The order ID is then stored on the form and included in the final
    certificate request submission.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid request body."}), 400

    order_id = data.get("orderID", "")
    if not isinstance(order_id, str) or not order_id.strip():
        return jsonify({"status": "error", "message": "Missing PayPal order ID."}), 400

    try:
        token = _paypal_token()
        resp = http.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{order_id.strip()}/capture",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return jsonify({"status": "success", "capture": resp.json()})
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Payment capture failed. Please try again.",
        }), 500


@api_routes.route("/data", methods=["POST"])
def receive_data():
    """Accept a JSON payload from the frontend, validate and sanitize it,
    then echo the clean version back with a success status.

    Returns 400 with a descriptive error message if any field is missing,
    has the wrong type, or contains a value outside its allowed set.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid request body."}), 400

    form_type = data.get("formType", "")

    if form_type == "certificateRequest":
        reason = data.get("reasonFor", "")
        if reason not in _ALLOWED_REASONS:
            return jsonify({"status": "error", "message": "Invalid reason for absence."}), 400

        other_reason = _sanitize(data.get("otherReason", ""), max_length=300)
        if reason == "other" and not other_reason:
            return jsonify({"status": "error", "message": "Please specify your reason for absence."}), 400

        surname = _sanitize(data.get("surname", ""), max_length=100)
        given_name = _sanitize(data.get("givenName", ""), max_length=100)
        if not surname or not given_name:
            return jsonify({"status": "error", "message": "Surname and given name are required."}), 400

        dob = data.get("dateOfBirth", "")
        if not _valid_date(dob):
            return jsonify({"status": "error", "message": "Invalid date of birth."}), 400

        email = data.get("email", "")
        if not _valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email address."}), 400

        start_date = data.get("absenceStartDate", "")
        end_date = data.get("absenceEndDate", "")
        if not _valid_date(start_date) or not _valid_date(end_date):
            return jsonify({"status": "error", "message": "Invalid absence dates."}), 400
        if end_date < start_date:
            return jsonify({"status": "error", "message": "End date must be on or after start date."}), 400

        paypal_order_id = _sanitize(data.get("paypalOrderId", ""), max_length=50)
        if not paypal_order_id:
            return jsonify({"status": "error", "message": "Payment has not been completed."}), 400

        clean = {
            "formType": "certificateRequest",
            "reasonFor": reason,
            "otherReason": other_reason,
            "surname": surname,
            "givenName": given_name,
            "dateOfBirth": dob,
            "email": _sanitize(email, max_length=254),
            "absenceStartDate": start_date,
            "absenceEndDate": end_date,
            "paypalOrderId": paypal_order_id,
        }

    elif form_type == "contactMessage":
        name = _sanitize(data.get("name", ""), max_length=200)
        email = data.get("email", "")
        message = _sanitize(data.get("message", ""), max_length=2000)
        if not name:
            return jsonify({"status": "error", "message": "Name is required."}), 400
        if not _valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email address."}), 400
        if not message:
            return jsonify({"status": "error", "message": "Message is required."}), 400
        clean = {
            "formType": "contactMessage",
            "name": name,
            "email": _sanitize(email, max_length=254),
            "message": message,
        }

    elif form_type == "general":
        clean = {
            "formType": "general",
            "name": _sanitize(data.get("name", ""), max_length=200),
        }

    else:
        return jsonify({"status": "error", "message": "Unknown form type."}), 400

    return jsonify({"status": "success", "received": clean})
