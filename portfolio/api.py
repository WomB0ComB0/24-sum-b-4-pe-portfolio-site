import json
from portfolio.mysql_db import Timeline, Hobbies, Projects
from flask import request, jsonify
from typing import Tuple, Type, Optional, List
from peewee import Model, DatabaseError, DoesNotExist
import logging

from portfolio.constants import StatusCodeLiteral

logger = logging.getLogger(__name__)


class APIBase:
    model: Type[Model]

    @classmethod
    def get_all(cls) -> Tuple[str, StatusCodeLiteral]:
        try:
            data = list(cls.model.select().dicts())
            return jsonify(data).get_data(as_text=True), 200
        except DatabaseError as e:
            logger.error("Database error on GET: %s", e)
            return jsonify({"error": str(e)}).get_data(as_text=True), 500

    @classmethod
    def get_by_id(cls, item_id: int) -> Tuple[str, StatusCodeLiteral]:
        try:
            item = cls.model.get_by_id(item_id)
            if item:
                return jsonify(item.__data__).get_data(as_text=True), 200
            else:
                return jsonify({"error": "Item not found"}).get_data(as_text=True), 404
        except DatabaseError as e:
            logger.error("Database error on GET by ID: %s", e)
            return jsonify({"error": str(e)}).get_data(as_text=True), 500

    @classmethod
    def create(cls) -> Tuple[str, StatusCodeLiteral]:
        try:
            data = request.get_json(force=True)
            logger.debug("POST Data: %s", data)

            def get_expected_keys(model_name: str) -> dict:
                match model_name:
                    case "Timeline":
                        return {
                            "timeline_id": "<int>",
                            "title": "<str>",
                            "description": "<str>",
                            "date": "<datetime>",
                            "image": "<str>",
                            "url": "<str>",
                        }
                    case "Hobbies":
                        return {
                            "hobbies_id": "<int>",
                            "name": "<str>",
                            "description": "<str>",
                            "image": "<str>",
                        }
                    case "Projects":
                        return {
                            "projects_id": "<int>",
                            "name": "<str>",
                            "description": "<str>",
                            "url": "<str>",
                            "language": "<str>",
                        }
                    case _:
                        return {}

            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        expected_keys = get_expected_keys(cls.model.__name__)
                        return (
                            jsonify(
                                {
                                    "error": f"Invalid data format: expected {expected_keys}"
                                }
                            ).get_data(as_text=True),
                            400,
                        )
                    cls.model.create(**item)
            elif isinstance(data, dict):
                cls.model.create(**data)
            else:
                expected_keys = get_expected_keys(cls.model.__name__)
                return (
                    jsonify(
                        {"error": f"Invalid data format: expected {expected_keys}"}
                    ).get_data(as_text=True),
                    400,
                )

            return (
                jsonify({"message": "Item(s) created successfully"}).get_data(
                    as_text=True
                ),
                201,
            )
        except DatabaseError as e:
            logger.error("Database error on POST: %s", e)
            return jsonify({"error": str(e)}).get_data(as_text=True), 500

    @classmethod
    def update(cls, item_id: int) -> Tuple[str, StatusCodeLiteral]:
        try:
            data = request.get_json(force=True)
            if not isinstance(data, dict):
                return (
                    jsonify({"error": "Invalid data format"}).get_data(as_text=True),
                    400,
                )
            cls.model.set_by_id(item_id, data)
            return (
                jsonify({"message": "Item updated successfully"}).get_data(
                    as_text=True
                ),
                200,
            )
        except DatabaseError as e:
            logger.error("Database error on PUT: %s", e)
            return jsonify({"error": str(e)}).get_data(as_text=True), 500

    @classmethod
    def delete(cls, item_id: int) -> Tuple[str, StatusCodeLiteral]:
        try:
            cls.model.delete_by_id(item_id)
            return (
                jsonify({"message": "Item deleted successfully"}).get_data(
                    as_text=True
                ),
                200,
            )
        except DatabaseError as e:
            logger.error("Database error on DELETE: %s", e)
            return jsonify({"error": str(e)}).get_data(as_text=True), 500

    @classmethod
    def delete_range(cls) -> Tuple[str, StatusCodeLiteral]:
        print(cls.model.__name__)
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
                    item = cls.model.get_by_id(i)
                    if item:
                        item.delete_instance()
                        deleted_count += 1
                    else:
                        errors.append(f"Item with id {i} not found")
                except DoesNotExist as e:
                    errors.append(f"Item with id {i} does not exist: {str(e)}")
                except DatabaseError as e:
                    errors.append(f"Error deleting item with id {i}: {str(e)}")

            if deleted_count > 0:
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
        except Exception as e:
            logger.error("Error in delete_range: %s", str(e))
            return jsonify({"error": str(e)}).get_data(as_text=True), 500

class APITimeline(APIBase):
    model = Timeline


class APIHobbies(APIBase):
    model = Hobbies


class APIProjects(APIBase):
    model = Projects
