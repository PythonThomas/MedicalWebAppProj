from flask import Blueprint, jsonify, request

api_routes = Blueprint("api_routes", __name__)

@api_routes.route("/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello from backend"})

@api_routes.route("/data", methods=["POST"])
def receive_data():
    data = request.json
    return jsonify({"received": data})