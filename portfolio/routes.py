from typing import List, Dict
import os
import requests
from dotenv import load_dotenv
from flask import request, jsonify, render_template, current_app as app
from portfolio.schemas import SchemaType
from portfolio.utils import ContactForm, JsonReader
from portfolio.auth import check_authentication
from portfolio.mysql_db import Projects, Hobbies, Timeline
from pydantic import ValidationError
from peewee import DatabaseError
import logging

load_dotenv()
base_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(base_path)

nav_menu: List[Dict[str, str]] = [
    {"name": "Home", "url": "/"},
    {"name": "Hobbies", "url": f"/{SchemaType.HOBBIES.value}"},
    {"name": "Projects", "url": f"/{SchemaType.PROJECTS.value}"},
    {"name": "Timeline", "url": f"/{SchemaType.TIMELINE.value}"},
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


@app.route(f"/{SchemaType.TIMELINE.value}", methods=["GET", "OPTIONS"])
def timeline():
    menu = active_menu(nav_menu, request.url)
    if request.method == "OPTIONS":
        return jsonify({"message": "GET, OPTIONS"})
    response = requests.get(
        f"{request.url_root}api/v1/{SchemaType.TIMELINE.value}",
        timeout=10,
        headers={"Authorization": f"{os.getenv('TOKEN')}"},
    )
    if response.content:
        print(response.json())
    else:
        print("Empty response")
    timeline_data = response.json()["timeline"]
    return render_template(
        "pages/timeline.jinja2",
        title="Timeline",
        url=os.getenv("URL"),
        menu=menu,
        timeline=timeline_data,
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
                message=request.form.get("message"),
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
            projects_data: list[Projects] = list(Projects.select())
            projects_list = [item.__data__ for item in projects_data]
            return jsonify({"projects": projects_list})
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "POST":
        try:
            data: dict = request.json
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
            data: dict = request.json
            if 'name' in data:
                Projects.update(**data).where(Projects.name == data["name"]).execute()
                return jsonify({"message": "Project updated successfully"})
            else:
                return jsonify({"error": "Name key is missing in the request data"}), 400
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "DELETE":
        try:
            data: dict = request.json
            if 'name' in data:
                Projects.delete().where(Projects.name == data["name"]).execute()
                return jsonify({"message": "Project deleted successfully"})
            else:
                return jsonify({"error": "Name key is missing in the request data"}), 400
        except DatabaseError as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, POST, PUT, DELETE, OPTIONS"})


@app.route(f"/api/v1/{SchemaType.HOBBIES.value}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@check_authentication
def api_hobbies() -> str:
    if request.method == "GET":
        return handle_get_hobbies()
    elif request.method == "POST":
        return handle_post_hobbies()
    elif request.method == "DELETE":
        return handle_delete_hobby()
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, POST, PUT, DELETE, OPTIONS"})
    else:
        return jsonify({"error": "Method not allowed"}), 405

def handle_delete_hobby():
    data = request.get_json()
    if 'name' in data:
        hobby = Hobbies.get_or_none(Hobbies.name == data['name'])
        if hobby:
            hobby.delete_instance()
            return jsonify({"message": "Hobby deleted successfully"})
        else:
            return jsonify({"error": "Hobby not found"}), 404
    else:
        return jsonify({"error": "Name key is missing in the request data"}), 400


@app.route(f"/api/v1/{SchemaType.HOBBIES.value}/<int:id>", methods=["GET", "PUT", "DELETE", "OPTIONS"])
@check_authentication
def api_hobbies_id(id: int) -> str:
    if request.method == "PUT":
        return handle_put_hobby(id)
    elif request.method == "DELETE":
        return handle_delete_hobby(id)
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, PUT, DELETE, OPTIONS"})


def handle_get_hobbies():
    try:
        hobbies_data: list[Hobbies] = list(Hobbies.select())
        hobbies_list = [item.__data__ for item in hobbies_data]
        return jsonify({"hobbies": hobbies_list})
    except DatabaseError as e:
        logger.error("Database error on GET: %s", e)
        return jsonify({"error": str(e)}), 500


def handle_post_hobbies():
    try:
        data: dict = request.json
        logger.debug("POST data: %s", data)
        if isinstance(data, list):
            for item in data:
                Hobbies.create(**item)
        else:
            Hobbies.create(**data)
        return jsonify({"message": "Hobbies added successfully"})
    except DatabaseError as e:
        logger.error("Database error on POST: %s", e)
        return jsonify({"error": str(e)}), 500


def handle_put_hobby(id: int):
    try:
        data: dict = request.json
        logger.debug("PUT data: %s", data)
        if 'name' in data:
            Hobbies.update(**data).where(Hobbies.id == id).execute()
            return jsonify({"message": "Hobby updated successfully"})
        else:
            return jsonify({"error": "Name key is missing in the request data"}), 400
    except DatabaseError as e:
        logger.error("Database error on PUT: %s", e)
        return jsonify({"error": str(e)}), 500


def handle_delete_hobby(id: int):
    try:
        Hobbies.delete().where(Hobbies.id == id).execute()
        return jsonify({"message": "Hobby deleted successfully"})
    except DatabaseError as e:
        logger.error("Database error on DELETE: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route(f"/api/v1/{SchemaType.TIMELINE.value}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@check_authentication
def api_timeline() -> str:
    if request.method == "GET":
        return handle_get_timeline()
    elif request.method == "POST":
        return handle_post_timeline()
    elif request.method == "PUT":
        return handle_put_timeline()
    elif request.method == "DELETE":
        return handle_delete_timeline()
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, POST, PUT, DELETE, OPTIONS"})


def handle_get_timeline():
    try:
        timeline_data: list[Timeline] = list(Timeline.select().order_by(Timeline.date.desc()))
        timeline_list = [item.__data__ for item in timeline_data]
        return jsonify({"timeline": timeline_list})
    except DatabaseError as e:
        logger.error("Database error on GET: %s", e)
        return jsonify({"error": str(e)}), 500


def handle_post_timeline():
    try:
        data = request.json
        logger.debug("POST data: %s", data)
        if isinstance(data, list):
            for item in data:
                Timeline.create(**item)
        else:
            Timeline.create(**data)
        return jsonify({"message": "Timeline added successfully"})
    except DatabaseError as e:
        logger.error("Database error on POST: %s", e)
        return jsonify({"error": str(e)}), 500


def handle_put_timeline():
    try:
        data = request.json
        logger.debug("PUT data: %s", data)
        if isinstance(data, list):
            for item in data:
                Timeline.update(**item).where(Timeline.title == item["title"]).execute()
        else:
            Timeline.update(**data).where(Timeline.title == data["title"]).execute()
        return jsonify({"message": "Timeline updated successfully"})
    except DatabaseError as e:
        logger.error("Database error on PUT: %s", e)
        return jsonify({"error": str(e)}), 500


def handle_delete_timeline():
    try:
        data: dict = request.json
        if 'title' in data:
            Timeline.delete().where(Timeline.title == data["title"]).execute()
            return jsonify({"message": "Timeline deleted successfully"})
        else:
            return jsonify({"error": "Title key is missing in the request data"}), 400
    except DatabaseError as e:
        logger.error("Database error on DELETE: %s", e)
        return jsonify({"error": str(e)}), 500

logger = logging.getLogger(__name__)