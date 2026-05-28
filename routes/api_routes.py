"""API routes blueprint

This blueprint contains JSON API endpoints consumed by the frontend. It is
registered in the main application under the `/api` URL prefix (so the final
endpoints are `/api/hello`, `/api/data`, `/api/paypal/create-order`,
`/api/paypal/capture-order`, and `/api/send-certificate`).
"""

import html
import os
from base64 import b64encode
from datetime import datetime

import requests as http
from flask import Blueprint, jsonify, request

from database import (
    get_certificate_request,
    save_certificate_request,
    save_contact_message,
)
from email_service import send_certificate_email

api_routes = Blueprint("api_routes", __name__)

# PayPal API base URL — defaults to sandbox; set PAYPAL_BASE_URL in .env for production
PAYPAL_BASE = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

# Fixed certificate processing fee charged at payment step
CERT_PRICE_AUD = "12.99"

# Only these values are accepted for the "reason for absence" field.
# Any other value is rejected with a 400 error to prevent unexpected data.
_ALLOWED_REASONS = {"sick_leave", "carers_leave", "other"}


# ============================================
# SECURITY HELPERS
# ============================================
# All user-supplied values must pass through these helpers before being stored
# or returned. They prevent XSS (cross-site scripting) and injection attacks.

def _sanitize(value, max_length=500):
    # Convert <, >, &, ", ' to their HTML entities so they can never be
    # interpreted as code if the value is later rendered in a web page.
    # Strip surrounding whitespace, then cut the string to max_length.
    if not isinstance(value, str):
        return ""
    return html.escape(value.strip())[:max_length]


def _valid_date(value):
    # strptime raises ValueError for anything that isn't a real YYYY-MM-DD date,
    # so a separate regex check is not needed — one try/except covers both
    # format validation and calendar correctness (e.g. rejects 2024-02-30).
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _valid_email(value):
    # Basic structural check without regex:
    #   1. Must be a string with exactly one @ sign.
    #   2. The part before @ (local) must be 1–64 characters.
    #   3. The part after @ (domain) must be 1–255 characters.
    #   4. No whitespace anywhere (spaces are never valid in an email address).
    # This is intentionally lightweight — full RFC 5322 parsing is overkill
    # for a form email field.
    if not isinstance(value, str):
        return False
    value = value.strip()
    if value.count("@") != 1:
        return False
    local, domain = value.split("@")
    return (
        1 <= len(local) <= 64
        and 1 <= len(domain) <= 255
        and " " not in value
        and "\t" not in value
    )


# ============================================
# PAYPAL HELPERS
# ============================================

def _paypal_token():
    # Read PayPal credentials from environment variables (set in .env).
    client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    secret = os.getenv("PAYPAL_CLIENT_SECRET", "")

    # PayPal's OAuth endpoint expects credentials as Base64-encoded "id:secret".
    creds = b64encode(f"{client_id}:{secret}".encode()).decode()

    # Exchange credentials for a short-lived access token (~9 hour expiry).
    # This token is then passed as a Bearer header on every PayPal API call.
    resp = http.post(
        f"{PAYPAL_BASE}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data="grant_type=client_credentials",
        timeout=10,
    )
    resp.raise_for_status()  # raises an exception if PayPal returns an error status
    return resp.json()["access_token"]


# ============================================
# API ENDPOINTS
# ============================================

@api_routes.route("/hello", methods=["GET"])
def hello():
    # Simple smoke-test endpoint — confirms the backend is reachable.
    return jsonify({"message": "Hello from Python backend!"})


@api_routes.route("/paypal/create-order", methods=["POST"])
def paypal_create_order():
    # Called by the PayPal JS SDK's createOrder callback.
    # We create a CAPTURE-intent order on PayPal's servers for $12.99 AUD.
    # PayPal returns an order ID which the SDK uses to open the payment popup.
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
        # Return only the order ID — the SDK needs this to open the popup.
        return jsonify({"id": resp.json()["id"]})
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Could not create PayPal order. Please try again.",
        }), 500


@api_routes.route("/paypal/capture-order", methods=["POST"])
def paypal_capture_order():
    # Called by the frontend's onApprove callback after the user approves payment.
    # Capturing the order tells PayPal to actually move the funds.
    # Until this call succeeds, no money has been collected.
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
        # Return the full PayPal capture response so the frontend can read
        # the payment status and store the order ID on the form.
        return jsonify({"status": "success", "capture": resp.json()})
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Payment capture failed. Please try again.",
        }), 500


@api_routes.route("/data", methods=["POST"])
def receive_data():
    # Parse the incoming JSON body. silent=True returns None instead of
    # raising an exception if the body is missing or not valid JSON.
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid request body."}), 400

    # Route to the correct validation block based on which form was submitted.
    form_type = data.get("formType", "")

    if form_type == "certificateRequest":
        # Validate reason against a fixed allow-list — reject anything unexpected.
        reason = data.get("reasonFor", "")
        if reason not in _ALLOWED_REASONS:
            return jsonify({"status": "error", "message": "Invalid reason for absence."}), 400

        # Only required when "other" is selected; sanitize but allow empty otherwise.
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

        # String comparison works for ISO dates (YYYY-MM-DD) because the format
        # sorts lexicographically in the same order as chronologically.
        if end_date < start_date:
            return jsonify({"status": "error", "message": "End date must be on or after start date."}), 400

        paypal_order_id = _sanitize(data.get("paypalOrderId", ""), max_length=50)
        if not paypal_order_id:
            return jsonify({"status": "error", "message": "Payment has not been completed."}), 400

        # Build the clean dict from validated/sanitized values only —
        # never pass the raw request data directly to the database.
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

        # Persist to PostgreSQL and attach the generated UUID to the response
        # so the caller knows which record to reference when sending the email.
        try:
            user_id = save_certificate_request(clean)
            clean["userId"] = user_id
        except Exception:
            return jsonify({"status": "error", "message": "Failed to save request. Please try again."}), 500

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

        try:
            save_contact_message(clean)
        except Exception:
            return jsonify({"status": "error", "message": "Failed to save message. Please try again."}), 500

    elif form_type == "general":
        clean = {
            "formType": "general",
            "name": _sanitize(data.get("name", ""), max_length=200),
        }

    else:
        return jsonify({"status": "error", "message": "Unknown form type."}), 400

    return jsonify({"status": "success", "received": clean})


@api_routes.route("/send-certificate", methods=["POST"])
def send_certificate():
    # Accepts a userId (UUID string), fetches the matching certificate request
    # from the database, generates a PDF, and emails it to the stored address.
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid request body."}), 400

    user_id = data.get("userId", "")
    if not isinstance(user_id, str) or not user_id.strip():
        return jsonify({"status": "error", "message": "userId is required."}), 400

    # Look up the record — returns None if the UUID doesn't exist in the database.
    try:
        record = get_certificate_request(user_id.strip())
    except Exception:
        return jsonify({"status": "error", "message": "Database error."}), 500

    if record is None:
        return jsonify({"status": "error", "message": "No request found for that userId."}), 404

    # Generate the PDF and send it to the patient's stored email address.
    try:
        send_certificate_email(record["email"], record)
    except Exception:
        return jsonify({"status": "error", "message": "Failed to send email. Please try again."}), 500

    return jsonify({"status": "success", "message": f"Certificate sent to {record['email']}."})
