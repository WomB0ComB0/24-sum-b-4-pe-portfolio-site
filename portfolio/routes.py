import logging
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from dotenv import load_dotenv
from flask import current_app as app
from flask import g, jsonify, render_template, request
from peewee import DatabaseError
from pydantic import ValidationError
from flask_caching import Cache

from portfolio.auth import check_authentication
from portfolio.db import Database
from portfolio.mysql_db import Hobbies, Projects, Timeline
from portfolio.schemas import (
    AboutSchema,
    EducationSchema,
    LandingSchema,
    PlacesSchema,
    SchemaType,
    WorkSchema,
)
from portfolio.utils import ContactForm
from portfolio.constants import StatusCodeLiteral
from portfolio.constants import columns

load_dotenv()

logger = logging.getLogger(__name__)

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})

base_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(base_path)

test_database_path = os.path.join(root_path, "tests", "unit", "test_portfolio.db")


def get_db() -> Database:
    """
    Get the database connection.
    """
    if "db" not in g:
        g.db = Database(
            os.path.join(
                root_path,
                f"{test_database_path if os.getenv('TESTING') == 'True' else 'portfolio.db'}",
            )
        )
    return g.db


@app.teardown_appcontext
def close_db(_error: Optional[Exception]) -> None:
    """
    Close the database connection.
    """
    try:
        logger.info("Closing database connection")
        db = g.pop("db", None)
        if db is not None:
            db.close_connection()
    except Exception as e:
        logger.error("Error closing database connection: %s", e)
        raise e


connect = get_db()

connect.create_table(
    "education",
    EducationSchema(
        institution="",
        degree="",
        startDate="",
        endDate="",
        logo="",
        description="",
        skills="",
        id=0,
    ).json(),
)
connect.create_table(
    "places",
    PlacesSchema(
        name="",
        description="",
        lat=0,
        lng=0,
        id=0,
    ).json(),
)
connect.create_table(
    "work",
    WorkSchema(
        logo="",
        company="",
        title="",
        type="",
        location="",
        startDate="",
        endDate="",
        description="",
        id=0,
    ).json(),
)
connect.create_table(
    "about",
    AboutSchema(
        description="",
        image="",
        id=0,
    ).json(),
)


@app.route("/", methods=["GET", "OPTIONS"])
@cache.cached(timeout=3000)
def index() -> str:
    """
    Render the landing page.
    """
    if request.method == "OPTIONS":
        return jsonify({"message": "GET, OPTIONS"})

    places_data = connect.read_data(
        "places", ["name", "description", "lat", "lng", "id"]
    )
    educations = connect.read_data(
        "education",
        [
            "institution",
            "degree",
            "startDate",
            "endDate",
            "logo",
            "description",
            "skills",
            "id",
        ],
    )
    work_experiences = connect.read_data(
        "work",
        [
            "logo",
            "company",
            "title",
            "type",
            "location",
            "startDate",
            "endDate",
            "description",
            "id",
        ],
    )
    about = connect.read_data("about", ["description", "image", "id"])
    work_experiences = format_data(work_experiences, ["description"])
    educations = format_data(educations, ["description"])

    return render_template(
        "landing.jinja2",
        url=os.getenv("URL"),
        about=about[0] if about else {},
        places=places_data,
        educations=educations,
        work_experiences=work_experiences,
    )


@app.route(f"/{SchemaType.HOBBIES.value}", methods=["GET", "OPTIONS"])
@cache.cached(timeout=3000)
def hobbies() -> str:
    """
    Render the hobbies page.
    """
    if request.method == "OPTIONS":
        return jsonify({"message": "Options"}).get_data(as_text=True)
    response = requests.get(
        f"{request.url_root}api/v1/{SchemaType.HOBBIES.value}",
        timeout=10,
        headers={"Authorization": f"{os.getenv('TOKEN')}"},
    )
    response.raise_for_status()
    hobbies_data = response.json()["hobbies"]
    return render_template(
        "pages/hobbies.jinja2",
        title="Hobbies",
        url=os.getenv("URL"),
        hobbies=hobbies_data,
    )


@app.route(f"/{SchemaType.PROJECTS.value}", methods=["GET", "OPTIONS"])
@cache.cached(timeout=3000)
def projects() -> str:
    """
    Render the projects page.
    """
    if request.method == "OPTIONS":
        return jsonify({"message": "Options"}).get_data(as_text=True)
    response = requests.get(
        f"{request.url_root}api/v1/{SchemaType.PROJECTS.value}",
        timeout=10,
        headers={"Authorization": f"{os.getenv('TOKEN')}"},
    )
    response.raise_for_status()
    projects_data = response.json()["projects"]
    return render_template(
        "pages/projects.jinja2",
        title="Projects",
        url=os.getenv("URL"),
        projects=projects_data,
    )


@app.route(f"/{SchemaType.TIMELINE.value}", methods=["GET", "OPTIONS"])
@cache.cached(timeout=3000)
def timeline() -> str:
    """
    Render the timeline page.
    """
    if request.method == "OPTIONS":
        return jsonify({"message": "GET, OPTIONS"}).get_data(as_text=True)
    response = requests.get(
        f"{request.url_root}api/v1/{SchemaType.TIMELINE.value}",
        timeout=10,
        headers={"Authorization": f"{os.getenv('TOKEN')}"},
    )
    response.raise_for_status()
    if response.content:
        print(response.json())
    else:
        print("Empty response")
    timeline_data = response.json()["timeline"]
    return render_template(
        "pages/timeline.jinja2",
        title="Timeline",
        url=os.getenv("URL"),
        timeline=timeline_data,
    )


@app.route("/contact", methods=["GET", "POST", "OPTIONS"])
def contact() -> str:
    """
    Handle contact form submission.
    """
    if request.method == "POST":
        try:
            form_data = ContactForm(
                name=request.form.get("name", ""),
                profession=request.form.get("profession", ""),
                company=request.form.get("company", ""),
                email=request.form.get("email", ""),
                subject=request.form.get("subject", ""),
                message=request.form.get("message", ""),
            )
            assert form_data is not None
            invalidate_cache()
            return jsonify({"message": "Form submitted successfully"}).get_data(
                as_text=True
            )
        except ValidationError as e:
            return (
                jsonify({"message": "Validation error", "errors": e.errors()}).get_data(
                    as_text=True
                ),
                400,
            )
    elif request.method == "OPTIONS":
        return jsonify({"message": "Options"}).get_data(as_text=True)
    return render_template(
        "pages/contact.jinja2", title="Contact", url=os.getenv("URL")
    )


@app.errorhandler(404)
def not_found(e: Union[Exception, TypeError]) -> str:
    """
    Handle 404 errors.
    """
    return render_template(
        "client/404.jinja2", title="404", description=e, url=os.getenv("URL")
    )


# API
@app.route("/api/v1/landing", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@check_authentication
def api_landing() -> Tuple[str, StatusCodeLiteral]:
    """
    Get all landing data from the database.
    """
    db = get_db()
    if request.method == "GET":
        return handle_get_landing(db)
    elif request.method == "POST":
        return handle_post_landing(db)
    elif request.method == "PUT":
        return handle_put_landing_alter(db)
    elif request.method == "DELETE":
        return handle_delete_landing_range(db)
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, POST, PUT, DELETE, OPTIONS"}).get_data(
            as_text=True
        )
    else:
        return jsonify({"error": "Method not allowed"}).get_data(as_text=True), 405


@app.route("/api/v1/landing/<int:item_id>", methods=["GET", "PUT", "DELETE", "OPTIONS"])
@cache.cached(timeout=3000)
@check_authentication
def api_landing_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Handle landing API requests.
    """
    db = get_db()
    if request.method == "GET":
        return handle_get_landing_id(db, item_id)
    elif request.method == "PUT":
        return handle_put_landing(db, item_id)
    elif request.method == "DELETE":
        return handle_delete_landing_id(db, item_id)
    elif request.method == "OPTIONS":
        return jsonify({"message": "GET, PUT, DELETE, OPTIONS"}).get_data(as_text=True)
    else:
        return jsonify({"error": "Method not allowed"}).get_data(as_text=True), 405


def handle_get_landing(db: Database) -> str:
    """
    Get all landing data from the database.
    """
    try:
        education_data = db.read_data(
            "education",
            [
                "institution",
                "degree",
                "startDate",
                "endDate",
                "logo",
                "description",
                "skills",
                "id",
            ],
        )
        places_data = db.read_data(
            "places",
            ["name", "description", "lat", "lng", "id"],
        )
        work_data = db.read_data(
            "work",
            [
                "logo",
                "company",
                "title",
                "type",
                "location",
                "startDate",
                "endDate",
                "description",
                "id",
            ],
        )
        about_data = db.read_data("about", ["description", "image", "id"])

        landing_data = LandingSchema(
            education=education_data,
            places=places_data,
            work=work_data,
            about=about_data[0] if about_data else {},
        ).json()
        return jsonify(landing_data).get_data(as_text=True)
    except sqlite3.DatabaseError as e:
        logger.error("Error in handle_get_landing: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


def handle_get_landing_id(db: Database, item_id: int) -> str:
    try:
        query_string: Optional[str] = request.args.get("section")
        if query_string:
            if query_string in columns:
                result = db.read_data(query_string, columns[query_string])
                if 0 <= item_id < len(result):
                    return jsonify({query_string: result[item_id]}).get_data(
                        as_text=True
                    )
                else:
                    return (
                        jsonify({"error": "Index out of range"}).get_data(as_text=True),
                        404,
                    )
            else:
                return jsonify({"error": "Invalid section"}).get_data(as_text=True), 400
        else:
            return (
                jsonify({"error": "Section not specified"}).get_data(as_text=True),
                400,
            )
    except Exception as e:
        logger.error("Error in handle_get_landing_id: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


def handle_post_landing(db: Database) -> Tuple[str, StatusCodeLiteral]:
    try:
        data = request.get_json(force=True)
        if not isinstance(data, dict):
            logger.error("Invalid data type received: %s", type(data))
            return (
                jsonify(
                    {"error": "Invalid data format. Expected a JSON object."}
                ).get_data(as_text=True),
                400,
            )

        if "metadata" in data:
            del data["metadata"]

        for section, section_data in data.items():
            if isinstance(section_data, list):
                for item in section_data:
                    if isinstance(item, dict):
                        db.insert_data(section, item)
                    else:
                        logger.error(
                            "Invalid data format for item in section %s: %s",
                            section,
                            type(item),
                        )
                        return (
                            jsonify(
                                {
                                    "error": f"Invalid data format for item in section {section}"
                                }
                            ).get_data(as_text=True),
                            400,
                        )
            elif isinstance(section_data, dict):
                db.insert_data(section, section_data)
            else:
                logger.error(
                    "Invalid data format for section %s: %s",
                    section,
                    type(section_data),
                )
                return (
                    jsonify(
                        {"error": f"Invalid data format for section {section}"}
                    ).get_data(as_text=True),
                    400,
                )
        invalidate_cache()
        return jsonify({"message": "Data added successfully"}).get_data(as_text=True)
    except Exception as e:
        logger.error("Unexpected error in handle_post_landing: %s", str(e))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


# TODO: Fix this, handle cases for all data types which enclose string values
# TODO: Overhaul
def handle_put_landing_alter(db: Database) -> Tuple[str, StatusCodeLiteral]:
    try:
        data = request.json
        if (
            data
            and isinstance(data, dict)
            and "alter_table" in data
            and ("add_column" in data or "modify_column" in data)
        ):

            table_name: str = data["alter_table"]
            conn, cursor = db.get_connection()

            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns: List[Tuple[str, str, str]] = cursor.fetchall()

            new_table_name: str = f"{table_name}_new"
            create_query: str = f"CREATE TABLE {new_table_name} ("

            if "add_column" in data:
                new_column_def = data["add_column"]
                create_query += f"{new_column_def}, "

            column_defs: List[str] = []
            for col in existing_columns:
                col_name, col_type = col[1], col[2]
                if "modify_column" in data and col_name == data["modify_column"]:
                    from_type: Optional[str] = request.args.get("from")
                    to_type: Optional[str] = request.args.get("to")
                    if from_type and to_type:
                        try:
                            new_type = db.convert_data_type(from_type, to_type)
                            col_type = new_type
                        except ValueError as e:
                            return (
                                jsonify({format("error: {}", str(e))}).get_data(
                                    as_text=True
                                ),
                                400,
                            )
                    else:
                        col_type = "TEXT"
                column_defs.append(f"{col_name} {col_type}")

            create_query += ", ".join(column_defs)
            create_query += ")"
            cursor.execute(create_query)

            old_columns = ", ".join([col[1] for col in existing_columns])
            if "add_column" in data:
                cursor.execute(
                    f"INSERT INTO {new_table_name} ({old_columns}) SELECT {old_columns} FROM {table_name}"
                )
            else:
                cursor.execute(
                    f"INSERT INTO {new_table_name} SELECT * FROM {table_name}"
                )

            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")

            conn.commit()

            action = "added new column" if "add_column" in data else "modified column"
            invalidate_cache()
            return (
                jsonify(
                    {"message": f"Table {table_name} altered successfully ({action})"}
                ).get_data(as_text=True),
                200,
            )
        else:
            return (
                jsonify({"error": "Invalid data for table alteration"}).get_data(
                    as_text=True
                ),
                400,
            )
    except sqlite3.DatabaseError as e:
        logger.error("Error in handle_put_landing_alter: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


def handle_put_landing(db: "Database", item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Update a landing data in the database.
    """
    try:
        query_string: Optional[str] = request.args.get("section")
        if query_string:
            if query_string in columns:
                data: Any = request.json
                if data is None:
                    return (
                        jsonify({"error": "Invalid request data"}).get_data(
                            as_text=True
                        ),
                        400,
                    )
                if "metadata" in data:
                    del data["metadata"]
                try:
                    logger.error(
                        "Executing SQL query: UPDATE %s SET %s WHERE id = %s",
                        query_string,
                        ", ".join([f"{k} = ?" for k in data.keys()]),
                        item_id,
                    )
                    db.update_data(
                        where_condition={"id": item_id},
                        table_name=query_string,
                        data=data,
                        index=item_id,
                    )
                    invalidate_cache()
                    return (
                        jsonify({"message": "Data updated successfully"}).get_data(
                            as_text=True
                        ),
                        200,
                    )
                except sqlite3.DatabaseError as e:
                    logger.error(
                        "Error in handle_put_landing (second exception): %s", str(e)
                    )
                    logger.error(format("error: {}", str(e)))
                    return jsonify({"error": str(e)}).get_data(as_text=True), 500
            else:
                return (
                    jsonify({"error": f"Invalid section {query_string}"}).get_data(
                        as_text=True
                    ),
                    400,
                )
        else:
            return (
                jsonify({"error": "Section not specified"}).get_data(as_text=True),
                400,
            )
    except sqlite3.DatabaseError as e:
        logger.error("Error in handle_put_landing (first exception): %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


def handle_delete_landing_range(db: "Database") -> Tuple[str, StatusCodeLiteral]:
    """
    Delete a range of landing data from the database.
    """
    errors: List[str] = []
    try:
        query_string: Optional[str] = request.args.get("section", None)
        start_string: Optional[str] = request.args.get("start", None)
        end_string: Optional[str] = request.args.get("end", None)

        # 🚩
        if not all([query_string, start_string, end_string]):
            return (
                jsonify({"error": "Missing required parameters"}).get_data(
                    as_text=True
                ),
                400,
            )

        start: int = int(start_string) if start_string else 0
        end: int = int(end_string) if end_string else 0
        deleted_count: int = 0

        for i in range(start, end + 1):
            try:
                db.delete_data(query_string, where_condition={"id": i})
                deleted_count += 1
            except sqlite3.DatabaseError as e:
                errors.append(f"Error deleting item with id {i}: {str(e)}")

        if deleted_count > 0:
            invalidate_cache()
            return (
                jsonify(
                    {
                        "message": f"{deleted_count} items deleted successfully",
                        "errors": errors,
                    }
                ).get_data(as_text=True),
                200,
            )
        else:
            return (
                jsonify({"error": "No items deleted", "errors": errors}).get_data(
                    as_text=True
                ),
                404,
            )
    except (Exception, sqlite3.DatabaseError) as e:
        logger.error("Error in handle_delete_landing_range: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_delete_landing_id(
    db: "Database", item_id: int
) -> Tuple[str, StatusCodeLiteral]:
    """
    Delete a landing data from the database.
    """
    try:
        query_string: Optional[str] = request.args.get("section")

        if query_string:
            if query_string in columns:
                data: Any = request.json
                if data is None:
                    return (
                        jsonify({"error": "Invalid request data"}).get_data(
                            as_text=True
                        ),
                        400,
                    )
                if "metadata" in data:
                    del data["metadata"]
                try:
                    logger.error(
                        "Executing SQL query: DELETE FROM %s WHERE id = %s",
                        query_string,
                        item_id,
                    )
                    db.delete_data(query_string, where_condition={"id": item_id})
                    invalidate_cache()
                    return (
                        jsonify({"message": "Data deleted successfully"}).get_data(
                            as_text=True
                        ),
                        200,
                    )
                except sqlite3.DatabaseError as e:
                    logger.error("Error in handle_delete_landing: %s", str(e))
                    logger.error(format("error: {}", str(e)))
                    return jsonify({"error": str(e)}).get_data(as_text=True), 500
        return (
            jsonify({"message": "All landing data deleted successfully"}).get_data(
                as_text=True
            ),
            200,
        )
    except sqlite3.DatabaseError as e:
        logger.error("Error in handle_delete_landing: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


@app.route(
    f"/api/v1/{SchemaType.PROJECTS.value}",
    methods=["GET", "POST", "DELETE", "OPTIONS"],
)
@check_authentication
def api_projects() -> Tuple[str, StatusCodeLiteral]:
    """
    Handle projects API requests.
    """
    match request.method:
        case "GET":
            return handle_get_projects()
        case "POST":
            return handle_post_projects()
        case "DELETE":
            return handle_delete_projects_range()
        case "OPTIONS":
            return (
                jsonify({"message": "GET, POST, DELETE, OPTIONS"}).get_data(
                    as_text=True
                ),
                200,
            )
        case _:
            return (
                jsonify({"error": "Method not allowed"}).get_data(as_text=True),
                405,
            )


@app.route(
    f"/api/v1/{SchemaType.PROJECTS.value}/<int:id>",
    methods=["GET", "PUT", "DELETE", "OPTIONS"],
)
@check_authentication
def api_projects_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    match request.method:
        case "GET":
            return handle_get_projects_id(item_id)
        case "PUT":
            return handle_put_projects(item_id)
        case "DELETE":
            return handle_delete_projects(item_id)
        case "OPTIONS":
            return (
                jsonify({"message": "GET, PUT, DELETE, OPTIONS"}).get_data(
                    as_text=True
                ),
                200,
            )
        case _:
            return (
                jsonify({"error": "Method not allowed"}).get_data(as_text=True),
                405,
            )


@cache.cached(timeout=300)
def handle_get_projects() -> Tuple[str, StatusCodeLiteral]:
    try:
        projects_data: list[Projects] = list(Projects.select())
        projects_list = [item.__data__ for item in projects_data]
        return jsonify({"projects": projects_list}).get_data(as_text=True), 200
    except DatabaseError as e:
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


@cache.cached(timeout=300)
def handle_get_projects_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    try:
        project = Projects.get_or_none(Projects.projects_id == item_id)
        return jsonify({"project": project.__data__}).get_data(as_text=True), 200
    except DatabaseError as e:
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_post_projects() -> Tuple[str, StatusCodeLiteral]:
    try:
        data: Any = request.json
        if data is None or not isinstance(data, dict):
            return (
                jsonify({"error": "Invalid request data"}).get_data(as_text=True),
                400,
            )
        if isinstance(data, list):
            for item in data:
                Projects.create(**item)
        else:
            Projects.create(**data)
        invalidate_cache()
        return (
            jsonify({"message": "Projects added successfully"}).get_data(as_text=True),
            200,
        )
    except DatabaseError as e:
        logger.error("Database error on POST: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_put_projects(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    try:
        data: Any = request.json
        if data is None or not isinstance(data, dict):
            return (
                jsonify({"error": "Invalid request data"}).get_data(as_text=True),
                400,
            )
        Projects.update(**data).where(Projects.projects_id == item_id).execute()
        invalidate_cache()
        return (
            jsonify({"message": "Project updated successfully"}).get_data(as_text=True),
            200,
        )
    except DatabaseError as e:
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


def handle_delete_projects(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    try:
        Projects.delete().where(Projects.projects_id == item_id).execute()
        invalidate_cache()
        return (
            jsonify({"message": "Project deleted successfully"}).get_data(as_text=True),
            200,
        )
    except DatabaseError as e:
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


def handle_delete_projects_range() -> Tuple[str, StatusCodeLiteral]:
    try:
        start_string: Optional[str] = request.args.get("start")
        end_string: Optional[str] = request.args.get("end")

        if not all([start_string, end_string]):
            return (
                jsonify({"error": "Missing required parameters"}).get_data(
                    as_text=True
                ),
                400,
            )

        start: int = int(start_string) - 1 if start_string else 0
        end: int = int(end_string) - 1 if end_string else 0
        deleted_count: int = 0
        errors: List[str] = []

        for i in range(start, end + 1):
            try:
                project = Projects.get_or_none(Projects.projects_id == i)
                if project:
                    project.delete_instance()
                    deleted_count += 1
            except DatabaseError as e:
                errors.append(f"Error deleting project with id {i}: {str(e)}")

        if deleted_count > 0:
            invalidate_cache()
            return (
                jsonify(
                    {
                        "message": f"{deleted_count} projects deleted successfully",
                        "errors": errors,
                    }
                ).get_data(as_text=True),
                200,
            )
        else:
            return (
                jsonify({"error": "No projects deleted", "errors": errors}).get_data(
                    as_text=True
                ),
                404,
            )
    except Exception as e:
        logger.error("Error in handle_delete_projects_range: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


@app.route(
    f"/api/v1/{SchemaType.HOBBIES.value}",
    methods=["GET", "POST", "DELETE", "OPTIONS"],
)
@check_authentication
def api_hobbies() -> Tuple[str, StatusCodeLiteral]:
    match request.method:
        case "GET":
            return handle_get_hobbies()
        case "POST":
            return handle_post_hobbies()
        case "DELETE":
            return handle_delete_hobbies_range()
        case "OPTIONS":
            return (
                jsonify({"message": "GET, POST, DELETE, OPTIONS"}).get_data(
                    as_text=True
                ),
                200,
            )
        case _:
            return (
                jsonify({"error": "Method not allowed"}).get_data(as_text=True),
                405,
            )


@app.route(
    f"/api/v1/{SchemaType.HOBBIES.value}/<int:id>",
    methods=["GET", "PUT", "DELETE", "OPTIONS"],
)
@check_authentication
def api_hobbies_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    match request.method:
        case "GET":
            return handle_get_hobbies_id(item_id)
        case "PUT":
            return handle_put_hobby_id(item_id)
        case "DELETE":
            return handle_delete_hobby_id(item_id)
        case "OPTIONS":
            return (
                jsonify({"message": "GET, PUT, DELETE, OPTIONS"}).get_data(
                    as_text=True
                ),
                200,
            )
        case _:
            return (
                jsonify({"error": "Method not allowed"}).get_data(as_text=True),
                405,
            )


@cache.cached(timeout=300)
def handle_get_hobbies() -> Tuple[str, StatusCodeLiteral]:
    """
    Get all hobbies from the database.
    """
    try:
        hobbies_data: list[Hobbies] = list(Hobbies.select())
        hobbies_list = [item.__data__ for item in hobbies_data]
        return jsonify({"hobbies": hobbies_list}).get_data(as_text=True), 200
    except DatabaseError as e:
        logger.error("Database error on GET: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


@cache.cached(timeout=300)
def handle_get_hobbies_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Get a hobby from the database.
    """
    try:
        hobby = Hobbies.get_or_none(Hobbies.hobbies_id == item_id)
        if hobby is None:
            return (
                jsonify({"error": "Hobby not found"}).get_data(as_text=True),
                404,
            )
        return jsonify({"hobby": hobby.__data__}).get_data(as_text=True), 200
    except DatabaseError as e:
        logger.error("Database error on GET: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_post_hobbies() -> Tuple[str, StatusCodeLiteral]:
    """
    Add a hobby to the database.
    """
    try:
        data: Any = request.json
        if data is None or not isinstance(data, dict):
            return (
                jsonify({"error": "Invalid request data"}).get_data(as_text=True),
                400,
            )
        if isinstance(data, list):
            for item in data:
                Hobbies.create(**item)
        else:
            Hobbies.create(**data)
        invalidate_cache()
        return (
            jsonify({"message": "Hobbies added successfully"}).get_data(as_text=True),
            200,
        )
    except DatabaseError as e:
        logger.error("Database error on POST: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_put_hobby_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Update a hobby in the database.
    """
    try:
        data: Any = request.json
        if data is None or not isinstance(data, dict):
            return (
                jsonify({"error": "Invalid request data"}).get_data(as_text=True),
                400,
            )
        Hobbies.update(**data).where(Hobbies.hobbies_id == item_id).execute()
        invalidate_cache()
        return (
            jsonify({"message": "Hobby updated successfully"}).get_data(as_text=True),
            200,
        )
    except DatabaseError as e:
        logger.error("Database error on PUT: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_delete_hobbies_range() -> Tuple[str, StatusCodeLiteral]:
    try:
        start_string: Optional[str] = request.args.get("start")
        end_string: Optional[str] = request.args.get("end")

        if not all([start_string, end_string]):
            return (
                jsonify({"error": "Missing required parameters"}).get_data(
                    as_text=True
                ),
                400,
            )

        start: int = int(start_string) - 1 if start_string else 0
        end: int = int(end_string) - 1 if end_string else 0
        deleted_count: int = 0
        errors: List[str] = []

        for i in range(start, end + 1):
            try:
                hobby = Hobbies.get_or_none(Hobbies.hobbies_id == i)
                if hobby:
                    hobby.delete_instance()
                    deleted_count += 1
            except DatabaseError as e:
                errors.append(f"Error deleting hobby with id {i}: {str(e)}")

        if deleted_count > 0:
            invalidate_cache()
            return (
                jsonify(
                    {
                        "message": f"{deleted_count} hobbies deleted successfully",
                        "errors": errors,
                    }
                ).get_data(as_text=True),
                200,
            )
        else:
            return (
                jsonify({"error": "No hobbies deleted", "errors": errors}).get_data(
                    as_text=True
                ),
                404,
            )
    except Exception as e:
        logger.error("Error in handle_delete_hobbies_range: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({"error": str(e)}).get_data(as_text=True), 500


def handle_delete_hobby_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Delete a hobby from the database.
    """
    try:
        Hobbies.delete().where(Hobbies.hobbies_id == item_id).execute()
        invalidate_cache()
        return (
            jsonify({"message": "Hobby deleted successfully"}).get_data(as_text=True),
            200,
        )
    except DatabaseError as e:
        logger.error("Database error on DELETE: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


@app.route(
    f"/api/v1/{SchemaType.TIMELINE.value}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
@check_authentication
def api_timeline() -> Tuple[str, StatusCodeLiteral]:
    """
    Handle timeline API requests.
    """
    match request.method:
        case "GET":
            return handle_get_timeline()
        case "POST":
            return handle_post_timeline()
        case "DELETE":
            return handle_delete_timeline_range()
        case "OPTIONS":
            return (
                jsonify({"message": "GET, POST, DELETE, OPTIONS"}).get_data(
                    as_text=True
                ),
                200,
            )
        case _:
            return (
                jsonify({"error": "Method not allowed"}).get_data(as_text=True),
                405,
            )


@app.route(
    f"/api/v1/{SchemaType.TIMELINE.value}/<int:item_id>",
    methods=["GET", "PUT", "DELETE", "OPTIONS"],
)
@check_authentication
def api_timeline_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    match request.method:
        case "GET":
            return handle_get_timeline_id(item_id)
        case "PUT":
            return handle_put_timeline(item_id)
        case "DELETE":
            return handle_delete_timeline_id(item_id)
        case "OPTIONS":
            return (
                jsonify({"message": "GET, PUT, DELETE, OPTIONS"}).get_data(
                    as_text=True
                ),
                200,
            )
        case _:
            return (
                jsonify({"error": "Method not allowed"}).get_data(as_text=True),
                405,
            )


@cache.cached(timeout=300)
def handle_get_timeline() -> Tuple[str, StatusCodeLiteral]:
    """
    Get all timeline data from the database.
    """
    try:
        timeline_data: list[Timeline] = list(
            Timeline.select().order_by(Timeline.date.desc())
        )
        if timeline_data is None:
            return (
                jsonify({"error": "No timeline data found"}).get_data(as_text=True),
                404,
            )
        timeline_list = [item.__data__ for item in timeline_data]
        return jsonify({"timeline": timeline_list}).get_data(as_text=True), 200
    except DatabaseError as e:
        logger.error("Database error on GET: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


@cache.cached(timeout=300)
def handle_get_timeline_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Get a timeline from the database.
    """
    try:
        timeline_data: list[Timeline] = list(
            Timeline.select().where(Timeline.timeline_id == item_id)
        )
        if timeline_data is None:
            return (
                jsonify({"error": "No timeline data found"}).get_data(as_text=True),
                404,
            )
        timeline_list = [item.__data__ for item in timeline_data]
        return jsonify({"timeline": timeline_list}).get_data(as_text=True), 200
    except DatabaseError as e:
        logger.error("Database error on GET: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_post_timeline() -> Tuple[str, StatusCodeLiteral]:
    """
    Add a timeline to the database.
    """
    try:
        data: Any = request.json
        if data is None or not isinstance(data, dict):
            return (
                jsonify({"error": "Invalid request data"}).get_data(as_text=True),
                400,
            )
        if isinstance(data, list):
            for item in data:
                Timeline.create(**item)
        else:
            Timeline.create(**data)
        invalidate_cache()
        return (
            jsonify({"message": "Timeline added successfully"}).get_data(as_text=True),
            200,
        )
    except DatabaseError as e:
        logger.error("Database error on POST: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_put_timeline(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Update a timeline in the database.
    """
    try:
        data: Any = request.json
        if data is None or not isinstance(data, dict):
            return (
                jsonify({"error": "Invalid request data"}).get_data(as_text=True),
                400,
            )
        if isinstance(data, list):
            for item in data:
                Timeline.update(**item).where(
                    Timeline.timeline_id == item["timeline_id"]
                ).execute()
        else:
            Timeline.update(**data).where(Timeline.timeline_id == item_id).execute()
        invalidate_cache()
        return (
            jsonify({"message": "Timeline updated successfully"}).get_data(
                as_text=True
            ),
            200,
        )
    except DatabaseError as e:
        logger.error("Database error on PUT: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_delete_timeline_range() -> Tuple[str, StatusCodeLiteral]:
    """
    Delete a range of timeline items from the database.
    """
    try:
        start_string: Optional[str] = request.args.get("start")
        end_string: Optional[str] = request.args.get("end")

        if not all([start_string, end_string]):
            return (
                jsonify({"error": "Missing required parameters"}).get_data(
                    as_text=True
                ),
                400,
            )

        start: int = int(start_string) if start_string else 0
        end: int = int(end_string) if end_string else 0
        deleted_count: int = 0
        errors: List[str] = []

        for i in range(start, end + 1):
            try:
                timeline_item = Timeline.get_or_none(Timeline.timeline_id == i)
                if timeline_item:
                    timeline_item.delete_instance()
                    deleted_count += 1
            except DatabaseError as e:
                errors.append(f"Error deleting timeline item with id {i}: {str(e)}")

        if deleted_count > 0:
            invalidate_cache()
            return (
                jsonify(
                    {
                        "message": f"{deleted_count} timeline items deleted successfully",
                        "errors": errors,
                    }
                ).get_data(as_text=True),
                200,
            )
        else:
            return (
                jsonify(
                    {"error": "No timeline items deleted", "errors": errors}
                ).get_data(as_text=True),
                404,
            )
    except Exception as e:
        logger.error("Error in handle_delete_timeline_range: %s", str(e))
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


def handle_delete_timeline_id(item_id: int) -> Tuple[str, StatusCodeLiteral]:
    """
    Delete a timeline from the database.
    """
    try:
        Timeline.delete().where(Timeline.timeline_id == item_id).execute()
        invalidate_cache()
        return (
            jsonify({"message": "Timeline deleted successfully"}).get_data(
                as_text=True
            ),
            200,
        )
    except DatabaseError as e:
        logger.error("Database error on DELETE: %s", e)
        logger.error(format("error: {}", str(e)))
        return jsonify({format("error: {}", str(e))}).get_data(as_text=True), 500


logger = logging.getLogger(__name__)

# Flask Utils


def invalidate_cache() -> None:
    cache.clear()


# JINJA Utils


# TODO: Revisit this function
def format_description(description: Any) -> Any:
    """
    Format the description to be displayed on the landing page.
    """
    if isinstance(description, list):
        return [
            item if isinstance(item, str) else "".join(item) for item in description
        ]
    elif isinstance(description, str):
        return [description]
    else:
        try:
            return [str(description)]
        except (TypeError, ValueError, AttributeError) as e:
            logger.error("Error in format_description: %s", str(e))
            return ["Error: Unable to format description"]


# TODO: Revisit this function
def clean_description(description: Any) -> str:
    """
    Clean the description to be displayed on the landing page.
    """
    if isinstance(description, list):
        return " ".join(description)
    return str(description)


# TODO: Revisit this function
def regex_replace(value: str, pattern: str, repl: str) -> str:
    """
    Replace the pattern in the value with the replacement.
    """
    return re.sub(pattern, repl, value)


# TODO: Revisit this function
def format_data(
    data_list: List[Dict[str, Any]], fields_to_format: List[str]
) -> List[Dict[str, Any]]:
    for item in data_list:
        for field in fields_to_format:
            if field in item:
                item[field] = format_description(item[field])
    return data_list


app.jinja_env.filters["format_description"] = format_description
app.jinja_env.filters["clean_description"] = clean_description
app.jinja_env.filters["regex_replace"] = regex_replace
