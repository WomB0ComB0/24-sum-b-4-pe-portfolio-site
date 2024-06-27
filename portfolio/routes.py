from typing import List, Dict
import os
from flask import current_app as app
from flask import request, jsonify, render_template
from dotenv import load_dotenv
from portfolio.utils import EmailValidator, JsonReader
from portfolio.auth import check_authentication

load_dotenv()

nav_menu: List[Dict[str, str]] = [
    {"name": "Home", "url": "/"},
    {"name": "Hobbies", "url": "/hobbies"},
    {"name": "Projects", "url": "/projects"},
    {"name": "Contact", "url": "/contact"},
]


def active_menu(menu: List[Dict[str, str]], url: str) -> str:
    for item in menu:
        if item["url"] == url:
            item["active"] = True
        else:
            item["active"] = False
    return menu


@app.route("/", methods=["GET", "OPTIONS", "HEAD"])
def index():
    menu = active_menu(nav_menu, request.url)
    if request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    elif request.method == "HEAD":
        return jsonify({"message": "Head"})
    return render_template(
        "landing.jinja2", title="MLH Fellow", url=os.getenv("URL"), menu=menu
    )


@app.route("/hobbies", methods=["GET", "OPTIONS", "HEAD"])
def hobbies():
    menu = active_menu(nav_menu, request.url)
    if request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    elif request.method == "HEAD":
        return jsonify({"message": "Head"})
    hobbies_data = JsonReader.read_data("static/json/hobbies.json")
    return render_template(
        "pages/hobbies.jinja2",
        title="MLH Fellow",
        url=os.getenv("URL"),
        menu=menu,
        hobbies=hobbies_data,
    )


@app.route("/projects", methods=["GET", "OPTIONS", "HEAD"])
def projects():
    menu = active_menu(nav_menu, request.url)
    if request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    elif request.method == "HEAD":
        return jsonify({"message": "Head"})
    projects_data = JsonReader.read_data("static/json/projects.json")
    return render_template(
        "pages/projects.jinja2",
        title="MLH Fellow",
        url=os.getenv("URL"),
        menu=menu,
        projects=projects_data,
    )


@app.route("/contact", methods=["GET", "POST", "OPTIONS", "HEAD"])
def contact():
    menu = active_menu(nav_menu, request.url)
    if request.method == "POST":
        email = request.form.get("email")
        if EmailValidator.validate_email(email):
            return jsonify({"message": "Email is valid"})
        else:
            return jsonify({"message": "Email is invalid"}), 400
    elif request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    elif request.method == "HEAD":
        return jsonify({"message": "Head"})
    return render_template(
        "pages/contact.jinja2", title="MLH Fellow", url=os.getenv("URL"), menu=menu
    )


@app.route("/*", methods=["GET", "OPTIONS", "HEAD"])
def not_found():
    menu = active_menu(nav_menu, request.url)
    return render_template(
        "client/404.jinja2", title="MLH Fellow", url=os.getenv("URL"), menu=menu
    )


# API
@app.route("/api/v1/projects", methods=["GET", "POST", "OPTIONS", "HEAD"])
@check_authentication
def api_projects() -> str:
    if request.method == "GET":
        return JsonReader.read_data("static/json/projects.json")
    elif request.method == "POST":
        return jsonify({"message": "Project created"})
    elif request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    elif request.method == "HEAD":
        return jsonify({"message": "Head"})


@app.route("/api/v1/hobbies", methods=["GET", "POST", "OPTIONS", "HEAD"])
@check_authentication
def api_hobbies() -> str:
    if request.method == "GET":
        return JsonReader.read_data("static/json/hobbies.json")
    elif request.method == "POST":
        return jsonify({"message": "Hobby created"})
    elif request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    elif request.method == "HEAD":
        return jsonify({"message": "Head"})
