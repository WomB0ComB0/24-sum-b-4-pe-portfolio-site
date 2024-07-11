from typing import List, Dict
import os
import requests
from dotenv import load_dotenv
from flask import request, jsonify, render_template, current_app as app
from portfolio.schemas import SchemaType
from portfolio.utils import ContactForm, JsonReader
from portfolio.auth import check_authentication
# from portfolio.db import Database
from portfolio.mysql_db import Projects, Hobbies
# import sqlite3
from pydantic import ValidationError

load_dotenv()
base_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(base_path)
from peewee import DatabaseError
# def get_db():
#     if "db" not in g:
#         g.db = Database(os.path.join(root_path, "portfolio.db"))
#     return g.db


# @app.teardown_appcontext
# def close_db(_error):
#     try:
#         print("Closing database connection")
#         db = g.pop("db", None)
#         if db is not None:
#             db.close_connection()
#     except Exception as e:
#         print(f"Error closing database connection: {e}")
#         raise e


# connect = get_db()
# connect.create_table(
#     "projects",
#     ProjectsSchema(
#         name="",
#         description="",
#         url="",
#         language="",
#     ).json(),
# )

# connect.create_table(
#     "hobbies",
#     HobbiesSchema(
#         name="",
#         description="",
#         image="",
#     ).json(),
# )

nav_menu: List[Dict[str, str]] = [
    {"name": "Home", "url": "/"},
    {"name": "Hobbies", "url": f"/{SchemaType.HOBBIES.value}"},
    {"name": "Projects", "url": f"/{SchemaType.PROJECTS.value}"},
    {"name": "Contact", "url": "/contact"},
]


def active_menu(menu: List[Dict[str, str]], url: str) -> str:
    for item in menu:
        if item["url"] == url:
            item["active"] = True
        else:
            item["active"] = False
    return menu


@app.route("/", methods=["GET", "OPTIONS"])
def index():
    # print(request.url)
    menu = active_menu(nav_menu, request.url)
    if request.method == "OPTIONS":
        return jsonify({"message": "GET, OPTIONS"})

    places_data = JsonReader("static/json/places.json").read_data()["places"]
    educations = JsonReader("static/json/education.json").read_data()["education"]
    work_experiences = JsonReader("static/json/work.json").read_data()["work"]
    about = JsonReader("static/json/about.json").read_data()["about"]

    return render_template(
        "landing.jinja2",
        url=os.getenv("URL"),
        menu=menu,
        about=about,
        places=places_data,
        educations=educations,
        work_experiences=work_experiences,
    )


@app.route(f"/{SchemaType.HOBBIES.value}", methods=["GET", "OPTIONS"])
def hobbies():
    menu = active_menu(nav_menu, request.url)
    if request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    response = requests.get(
        f"{request.url_root}api/v1/{SchemaType.HOBBIES.value}",
        timeout=10,
        headers={"Authorization": f"{os.getenv('TOKEN')}"},
    )
    hobbies_data = response.json()["hobbies"]
    return render_template(
        "pages/hobbies.jinja2",
        title="Hobbies",
        url=os.getenv("URL"),
        menu=menu,
        hobbies=hobbies_data,
    )


@app.route(f"/{SchemaType.PROJECTS.value}", methods=["GET", "OPTIONS"])
def projects():
    menu = active_menu(nav_menu, request.url)
    if request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    response = requests.get(
        f"{request.url_root}api/v1/{SchemaType.PROJECTS.value}",
        timeout=10,
        headers={"Authorization": f"{os.getenv('TOKEN')}"},
    )
    projects_data = response.json()["projects"]
    return render_template(
        "pages/projects.jinja2",
        title="Projects",
        url=os.getenv("URL"),
        menu=menu,
        projects=projects_data,
    )


@app.route("/contact", methods=["GET", "POST", "OPTIONS"])
def contact():
    menu = active_menu(nav_menu, request.url)
    if request.method == "POST":
        try:
            form_data = ContactForm(
                name=request.form.get("name"),
                profession=request.form.get("profession"),
                company=request.form.get("company"),
                email=request.form.get("email"),
                subject=request.form.get("subject"),
                message=request.form.get("message")
            )
            print(form_data)
            return jsonify({"message": "Form submitted successfully"})
        except ValidationError as e:
            return jsonify({"message": "Validation error", "errors": e.errors()}), 400
    elif request.method == "OPTIONS":
        return jsonify({"message": "Options"})
    return render_template(
        "pages/contact.jinja2", title="Contact", url=os.getenv("URL"), menu=menu
    )


@app.errorhandler(404)
def not_found(e):
    menu = active_menu(nav_menu, request.url)
    return render_template(
        "client/404.jinja2", title="404", url=os.getenv("URL"), menu=menu
    )


# API
@app.route(
    f"/api/v1/{SchemaType.PROJECTS.value}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
@check_authentication
def api_projects() -> str:
    if request.method == "GET":
        try:
            projects_data = Projects.select()
            return jsonify({"projects": projects_data})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "POST":
        try:
            data = request.json
            if isinstance(data, list):
                for item in data:
                    Projects.create(**item)
            else:
                Projects.create(**data)
            return jsonify({"message": "Projects added successfully"})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "PUT":
        try:
            data = request.json
            Projects.update(**data).where(Projects.name == data["name"]).execute()
            return jsonify({"message": "Project updated successfully"})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "DELETE":
        try:
            data = request.json
            Projects.delete().where(Projects.name == data["name"]).execute()
            return jsonify({"message": "Project deleted successfully"})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, POST, PUT, DELETE, OPTIONS"})


@app.route(
    f"/api/v1/{SchemaType.HOBBIES.value}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
@check_authentication
def api_hobbies() -> str:
    if request.method == "GET":
        try:
            hobbies_data = Hobbies.select()
            return jsonify({"hobbies": hobbies_data})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "POST":
        try:
            data = request.json
            if isinstance(data, list):
                for item in data:
                    Hobbies.create(**item)
            else:
                Hobbies.create(**data)
            return jsonify({"message": "Hobbies added successfully"})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "PUT":
        try:
            data = request.json
            Hobbies.update(**data).where(Hobbies.name == data["name"]).execute()
            return jsonify({"message": "Hobby updated successfully"})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "DELETE":
        try:
            data = request.json
            Hobbies.delete().where(Hobbies.name == data["name"]).execute()
            return jsonify({"message": "Hobby deleted successfully"})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, POST, PUT, DELETE, OPTIONS"})
