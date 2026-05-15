from flask import Blueprint, render_template

page_routes = Blueprint("page_routes", __name__)

@page_routes.route("/")
def index():
    return render_template("index.html")