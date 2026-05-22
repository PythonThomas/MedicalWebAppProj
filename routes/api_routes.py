"""API routes blueprint

This blueprint contains JSON API endpoints consumed by the frontend. It is
registered in the main application under the `/api` URL prefix (so the final
endpoints are `/api/hello` and `/api/data`).
"""

from flask import Blueprint, jsonify, request

api_routes = Blueprint("api_routes", __name__)


@api_routes.route("/hello", methods=["GET"])
def hello():
    """Return a simple greeting message as JSON.

    Matches the previous response shape used in `app.py`.
    """
    return jsonify({"message": "Hello from Python backend!"})


@api_routes.route("/data", methods=["POST"])
def receive_data():
    """Accept JSON payload from the frontend and echo it back with status."""
    data = request.json
    return jsonify({"status": "success", "received": data})