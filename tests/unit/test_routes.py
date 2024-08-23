import json
import sys
import os
import unittest
import importlib.metadata
import logging
from flask import g
import sqlite3
from typing import Dict, Any, List, Never

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from portfolio import create_app
from portfolio.db import Database
from portfolio.schemas import AboutSchema, EducationSchema, PlacesSchema, WorkSchema
from dotenv import load_dotenv
import requests

werzeug_version = importlib.metadata.version("werkzeug")
load_dotenv(dotenv_path=".env")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            logger.debug("Setting up class")
            cls.app = create_app()
            os.environ["TEST"] = "True"
            cls.client = cls.app.test_client()

            try:
                test_db_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "test_portfolio.db"
                )
                if os.path.exists(test_db_path):
                    os.remove(test_db_path)

                with cls.app.app_context():
                    g.db = Database(test_db_path)
                    g.db.create_table(
                        "about",
                        AboutSchema(description="", image="", id=1).json(),
                    )
                    g.db.create_table(
                        "education",
                        EducationSchema(
                            institution="",
                            degree="",
                            startDate="",
                            endDate="",
                            logo="",
                            description="",
                            skills="",
                            id=1,
                        ).json(),
                    )
                    g.db.create_table(
                        "places",
                        PlacesSchema(
                            name="", description="", lat=0.0, lng=0.0, id=1
                        ).json(),
                    )
                    g.db.create_table(
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
                            id=1,
                        ).json(),
                    )
                logger.info("SQLite tables created successfully")
            except sqlite3.DatabaseError as e:
                logger.error("SQLite Database error in setUpClass: %s", e)
                raise e
            except Exception as e:
                logger.error("Unexpected error in setUpClass: %s", e)
                raise e

        except Exception as e:
            logger.error("Error in setUpClass: %s", e)
            raise e

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ["TEST"] = "False"
        with cls.app.app_context():
            if hasattr(g, "db"):
                g.db.close_connection()

    def setUp(self) -> None:
        self.client = self.app.test_client()
        self.headers: Dict[str, str] = {
            "Authorization": os.getenv("TOKEN", ""),
            "HTTP_USER_AGENT": f"werkzeug/{werzeug_version}",
        }

    def test_regular(self,name: str, body: Any) -> None:
        try:
            logger.debug(f"Starting test_{name}_route")
            if body:
                post_response = self.client.post(
                    f"/api/v1/{name}",
                    headers=self.headers,
                    json=body,
                    content_type="application/json",
                )
                logger.error(
                    "POST Response: %s, Content: %s",
                    post_response.status_code,
                    post_response.data,
                )
                logger.debug(
                    "POST Response: %s, Content: %s",
                    post_response.status_code,
                    post_response.data,
                )
                self.assertEqual(post_response.status_code, 200)
            get_response = self.client.get(f"/api/v1/{name}", headers=self.headers)
            logger.error(
                "GET Response: %s, Content: %s",
                get_response.status_code,
                get_response.data,
            )
            logger.debug(
                "GET Response: %s, Content: %s",
                get_response.status_code,
                get_response.data,
            )
            self.assertEqual(get_response.status_code, 200)
            if body:
                put_response = self.client.put(
                    f"/api/v1/{name}/{body[-1]['{name}_id']}",
                    headers=self.headers,
                    body=body[-1]
                )
                logger.error(
                    "PUT Response: %s, Content: %s",
                    put_response.status_code,
                    put_response.data,
                )
                logger.debug(
                    "PUT Respons: %s, Content: %s",
                    put_response.status_code,
                    put_response.data
                )
            if body:
                delete_response = self.client.delete(
                    f"/api/v1/{name}/{body[-1]['{name}_id']}",
                    headers=self.headers,
                )
                logger.error(
                    "DELETE Response: %s, Content: %s",
                    delete_response.status_code,
                    delete_response.data,
                )
                logger.debug(
                    "DELETE Response: %s, Content: %s",
                    delete_response.status_code,
                    delete_response.data,
                )
                self.assertEqual(delete_response.status_code, 200)
        except requests.exceptions.RequestException as e:
            logger.error("Error in test_%s_route: %s", name, e)
            self.fail(f"test_%s_route failed: {e}")
    def test_range(self, name: str, body: Any) -> None:
        try:
            logger.debug(f"Starting test_{name}_range_deletion")
            post_respose = self.client.post(
                f"/api/v1/{name}",
                json=body,
                headers=self.headers
            )
            logger.error(
                "POS Response: %s, Content: %s",
                post_respose.status_code,
                post_respose.data
            )
            logger.debug(
                "POST Response: %s, Content: %s",
                post_respose.status__code,
                post_respose.data
            )
            self.assertEqual(post_respose.statu_code, 201)
            delete_respnse = self.client.delete(
                f"/api/v1/{name}?start=1&end=3",
                headers=self.headers
            )
            logger.error(
                "DELETE Response: %s, Content: %s",
                delete_respnse.status_code,
                delete_respnse.data
            )
            logger.debug(
                "DELETE Response: %s, Content: %s",
                delete_respnse.status_code,
                delete_respnse.data
            )
            self.assertEqual(delete_respnse.status_code, 200)
            response_data = delete_respnse.get_json()
            logger.error("Response data: %s", response_data)
            logger.debug("Response data: %s", response_data)
            self.assertIn("3 items deleted successfully", response_data["message"])

            get_response = self.client(f"/api/v1/{name}", headers=self.headers)
            logger.error(
                "GET Response: %s, Content: %s",
                get_response.status_code,
                get_response.data
            )
            logger.debug(
                "GET Response: %s, Content: %s",
                get_response.status_code,
                get_response.data
            )
            self.assertEqual(get_response.status_code, 200)
            res = get_response.get_json()
            logger.error(f"{name.upper()}: {res}")
            logger.debug(f"{name.upper()}: {res}")
            self.assertLessEqual(len(res), 1)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_{name}_range_deletion: {e}")
            self.fail(f"test_{name}_range_deletion: {e}")

    def test_landing_route(self) -> None:
        try:
            logger.debug("Starting test_landing_route")
            try:
                get_response = self.client.get("/api/v1/landing", headers=self.headers)
                logger.error(
                    "GET Response: %s, Content: %s",
                    get_response.status_code,
                    get_response.data,
                )
                logger.debug(
                    "GET Response: %s, Content: %s",
                    get_response.status_code,
                    get_response.data,
                )
                self.assertEqual(get_response.status_code, 200)
                self.assertIn("data", get_response.get_json())
                self.assertIn("metadata", get_response.get_json())
                logger.error("Response data: %s", get_response.get_json())
                logger.debug("Response data: %s", get_response.get_json())
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

            post_data: Dict[str, Any] = {
                "about": {
                    "description": "Test description",
                    "image": "test_image.jpg",
                    "id": 1,
                },
                "education": [
                    {
                        "institution": "Test University",
                        "degree": "Test Degree",
                        "startDate": "2020-01-01",
                        "endDate": "2024-01-01",
                        "logo": "test_logo.png",
                        "description": "Test education description",
                        "skills": "Skill 1, Skill 2",
                        "id": 1,
                    }
                ],
                "places": [
                    {
                        "name": "Test Place",
                        "description": "Test place description",
                        "lat": 40.7128,
                        "lng": -74.0060,
                        "id": 1,
                    }
                ],
                "work": [
                    {
                        "logo": "test_company_logo.png",
                        "company": "Test Company",
                        "title": "Test Title",
                        "type": "Full-time",
                        "location": "Test City",
                        "startDate": "2020-01-01",
                        "endDate": "2023-01-01",
                        "description": "Test work description",
                        "id": 1,
                    }
                ],
            }
            try:
                post_response = self.client.post(
                    "/api/v1/landing", json=post_data, headers=self.headers
                )
                logger.error(
                    "POST Response: %s, Content: %s",
                    post_response.status_code,
                    post_response.data,
                )
                logger.debug(
                    "POST Response: %s, Content: %s",
                    post_response.status_code,
                    post_response.data,
                )
                self.assertEqual(post_response.status_code, 201)
                self.assertIn("message", post_response.get_json())
                logger.error("Response data: %s", post_response.get_json())
                logger.debug("Response data: %s", post_response.get_json())
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

            try:
                options_response = self.client.options(
                    "/api/v1/landing", headers=self.headers
                )
                logger.error(
                    "OPTIONS Response: %s, Content: %s",
                    options_response.status_code,
                    options_response.data,
                )
                logger.debug(
                    "OPTIONS Response: %s, Content: %s",
                    options_response.status_code,
                    options_response.data,
                )
                self.assertEqual(options_response.status_code, 200)
                self.assertIn("message", options_response.get_json())
                logger.error("Response data: %s", options_response.get_json())
                logger.debug("Response data: %s", options_response.get_json())
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

            try:
                get_id_response = self.client.get(
                    "/api/v1/landing/1?section=education", headers=self.headers
                )
                logger.error(
                    "GET Response: %s, Content: %s",
                    get_id_response.status_code,
                    get_id_response.data,
                )
                logger.debug(
                    "GET Response: %s, Content: %s",
                    get_id_response.status_code,
                    get_id_response.data,
                )
                self.assertEqual(get_id_response.status_code, 200)
                self.assertIn("education", get_id_response.get_json())
                logger.error("Response data: %s", get_id_response.get_json())
                logger.debug("Response data: %s", get_id_response.get_json())
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

            put_data: Dict[str, Any] = {
                "institution": "Updated University",
                "degree": "Updated Degree",
                "startDate": "2020-01-01",
                "endDate": "2024-01-01",
                "logo": "updated_logo.png",
                "description": "Updated education description",
                "skills": "Updated Skill 1, Updated Skill 2",
                "id": 1,
            }
            try:
                put_response = self.client.put(
                    "/api/v1/landing/1?section=education",
                    json=put_data,
                    headers=self.headers,
                )
                logger.error(
                    "PUT Response: %s, Content: %s",
                    put_response.status_code,
                    put_response.data,
                )
                logger.debug(
                    "PUT Response: %s, Content: %s",
                    put_response.status_code,
                    put_response.data,
                )
                self.assertEqual(put_response.status_code, 200)
                self.assertIn("message", put_response.get_json())
                logger.debug("Response data: %s", put_response.get_json())
                logger.error("Response data: %s", put_response.get_json())
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

            try:
                delete_response = self.client.delete(
                    "/api/v1/landing/1?section=education", headers=self.headers
                )
                logger.error(
                    "DELETE Response: %s, Content: %s",
                    delete_response.status_code,
                    delete_response.data,
                )
                logger.debug(
                    "DELETE Response: %s, Content: %s",
                    delete_response.status_code,
                    delete_response.data,
                )
                self.assertEqual(delete_response.status_code, 200)
                self.assertIn("message", delete_response.get_json())
                logger.error("Response data: %s", delete_response.get_json())
                logger.debug("Response data: %s", delete_response.get_json())
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

            try:
                options_id_response = self.client.options(
                    "/api/v1/landing/1", headers=self.headers
                )
                logger.error(
                    "OPTIONS Response: %s, Content: %s",
                    options_id_response.status_code,
                    options_id_response.data,
                )
                logger.debug(
                    "OPTIONS Response: %s, Content: %s",
                    options_id_response.status_code,
                    options_id_response.data,
                )
                self.assertEqual(options_id_response.status_code, 200)
                self.assertIn("message", options_id_response.get_json())
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_landing_route: %s", e)
            self.fail(f"test_landing_route failed: {e}")


if __name__ == "__main__":
    unittest.main()
