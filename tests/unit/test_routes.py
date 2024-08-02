import unittest
import os
import importlib.metadata
import logging
from flask import g
import sqlite3
from typing import Dict, Any, List
from portfolio import create_app
from portfolio.db import Database
from portfolio.schemas import AboutSchema, EducationSchema, PlacesSchema, WorkSchema
from portfolio.mysql_db import Hobbies, Projects, Timeline
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

    def test_hobbies_route(self) -> None:
        try:
            logger.debug("Starting test_hobbies_route")
            get_response = self.client.get("/api/v1/hobbies", headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)

            post_data = {"name": "Test", "description": "Test", "image": "Test"}
            post_response = self.client.post(
                "/api/v1/hobbies",
                headers=self.headers,
                json=post_data,
                content_type="application/json",
            )
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)

            get_after_post = self.client.get("/api/v1/hobbies", headers=self.headers)
            hobbies = get_after_post.get_json()["hobbies"]
            # hobby_id = hobbies[0]["hobbies_id"]

            # delete_response = self.client.delete(
            #     f"/api/v1/hobbies/{hobby_id}",
            #     headers=self.headers,
            # )
            # logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            # self.assertEqual(delete_response.status_code, 200)

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_hobbies_route: %s", e)
            self.fail(f"test_hobbies_route failed: {e}")

    def test_projects_route(self) -> None:
        try:
            logger.debug("Starting test_projects_route")
            get_response = self.client.get("/api/v1/projects", headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)

            post_data = {
                "name": "Test",
                "description": "Test",
                "url": "Test",
                "language": "Test",
            }
            post_response = self.client.post(
                "/api/v1/projects",
                headers=self.headers,
                json=post_data,
                content_type="application/json",
            )
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)

            get_after_post = self.client.get("/api/v1/projects", headers=self.headers)
            projects = get_after_post.get_json()["projects"]
            project_id = projects[0]["projects_id"]

            delete_response = self.client.delete(
                f"/api/v1/projects/{project_id}",
                headers=self.headers,
            )
            logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            self.assertEqual(delete_response.status_code, 200)

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_projects_route: %s", e)
            self.fail(f"test_projects_route failed: {e}")

    def test_projects_range_deletion(self) -> None:
        try:
            logger.debug("Starting test_projects_range_deletion")
            post_data: List[Dict[str, Any]] = [
                {"name": "Project 1", "description": "Description 1", "url": "url1", "language": "Python"},
                {"name": "Project 2", "description": "Description 2", "url": "url2", "language": "JavaScript"},
                {"name": "Project 3", "description": "Description 3", "url": "url3", "language": "Java"},
            ]
            post_response = self.client.post("/api/v1/projects", json=post_data, headers=self.headers)
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)

            delete_response = self.client.delete("/api/v1/projects?start=1&end=2", headers=self.headers)
            logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            self.assertEqual(delete_response.status_code, 200)
            response_data = delete_response.get_json()
            self.assertIn("message", response_data)
            self.assertIn("2 projects deleted successfully", response_data["message"])

            get_response = self.client.get("/api/v1/projects", headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)
            projects = get_response.get_json()["projects"]
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0]["name"], "Project 3")

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_projects_range_deletion: %s", e)
            self.fail(f"test_projects_range_deletion failed: {e}")

    # def test_hobbies_range_deletion(self) -> None:
    #     try:
    #         logger.debug("Starting test_hobbies_range_deletion")
    #         post_data: List[Dict[str, Any]] = [
    #             {"name": "Hobby 1", "description": "Description 1", "image": "image1.jpg"},
    #             {"name": "Hobby 2", "description": "Description 2", "image": "image2.jpg"},
    #             {"name": "Hobby 3", "description": "Description 3", "image": "image3.jpg"},
    #         ]
    #         post_response = self.client.post("/api/v1/hobbies", json=post_data, headers=self.headers)
    #         logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
    #         self.assertEqual(post_response.status_code, 200)

    #         delete_response = self.client.delete("/api/v1/hobbies?start=1&end=3", headers=self.headers)
    #         logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
    #         self.assertEqual(delete_response.status_code, 200)
    #         response_data = delete_response.get_json()
    #         self.assertIn("message", response_data)
    #         self.assertIn("2 hobbies deleted successfully", response_data["message"])

            # get_response = self.client.get("/api/v1/hobbies", headers=self.headers)
            # logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            # self.assertEqual(get_response.status_code, 200)
            # hobbies = get_response.get_json()["hobbies"]
            # self.assertEqual(len(hobbies), 1)
            # self.assertEqual(hobbies[0]["name"], "Hobby 3")

        # except requests.exceptions.RequestException as e:
        #     logger.error("Error in test_hobbies_range_deletion: %s", e)
        #     self.fail(f"test_hobbies_range_deletion failed: {e}")

    def test_timeline_range_deletion(self) -> None:
        try:
            logger.debug("Starting test_timeline_range_deletion")
            post_data: List[Dict[str, Any]] = [
                {"title": "Event 1", "description": "Description 1", "date": "2023-01-01"},
                {"title": "Event 2", "description": "Description 2", "date": "2023-02-01"},
                {"title": "Event 3", "description": "Description 3", "date": "2023-03-01"},
            ]
            post_response = self.client.post("/api/v1/timeline", json=post_data, headers=self.headers)
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)

            # delete_response = self.client.delete("/api/v1/timeline?start=1&end=2", headers=self.headers)
            # logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            # self.assertEqual(delete_response.status_code, 200)
            # response_data = delete_response.get_json()
            # logger.error("Response data: %s", response_data)
            # self.assertIn("message", response_data)
            # self.assertIn("2 timeline items deleted successfully", response_data["message"])

            get_response = self.client.get("/api/v1/timeline", headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)
            timeline_items = get_response.get_json()["timeline"]
            logger.error("Timeline items: %s", timeline_items)
            self.assertEqual(len(timeline_items), 1)
            self.assertEqual(timeline_items[0]["title"], "Event 3")

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_timeline_range_deletion: %s", e)
            self.fail(f"test_timeline_range_deletion failed: {e}")

    def test_timeline_route(self) -> None:
        try:
            logger.debug("Starting test_timeline_route")
            get_response = self.client.get("/api/v1/timeline", headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)

            post_data = {"title": "Test", "description": "Test", "date": "2021-01-01"}
            post_response = self.client.post(
                "/api/v1/timeline",
                headers=self.headers,
                json=post_data,
                content_type="application/json",
            )
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)

            get_after_post = self.client.get("/api/v1/timeline", headers=self.headers)
            timeline_items = get_after_post.get_json()["timeline"]
            timeline_id = timeline_items[0]["timeline_id"]

            # delete_response = self.client.delete(
            #     f"/api/v1/timeline/{timeline_id}",
            #     headers=self.headers,
            # )
            # logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            # self.assertEqual(delete_response.status_code, 200)

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_timeline_route: %s", e)
            self.fail(f"test_timeline_route failed: {e}")

    def test_landing_route(self) -> None:
        try:
            logger.debug("Starting test_landing_route")
            get_response = self.client.get("/api/v1/landing", headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)
            self.assertIn("data", get_response.get_json())
            self.assertIn("metadata", get_response.get_json())

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
            post_response = self.client.post("/api/v1/landing", json=post_data, headers=self.headers)
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)
            self.assertIn("message", post_response.get_json())

            options_response = self.client.options("/api/v1/landing", headers=self.headers)
            logger.debug("OPTIONS Response: %s, Content: %s", options_response.status_code, options_response.data)
            self.assertEqual(options_response.status_code, 200)
            self.assertIn("message", options_response.get_json())

            get_id_response = self.client.get("/api/v1/landing/1?section=education", headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_id_response.status_code, get_id_response.data)
            self.assertEqual(get_id_response.status_code, 200)
            self.assertIn("education", get_id_response.get_json())

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
            put_response = self.client.put(
                "/api/v1/landing/1?section=education",
                json=put_data,
                headers=self.headers,
            )
            logger.debug("PUT Response: %s, Content: %s", put_response.status_code, put_response.data)
            self.assertEqual(put_response.status_code, 200)
            self.assertIn("message", put_response.get_json())

            # delete_response = self.client.delete("/api/v1/landing/1?section=education", headers=self.headers)
            # logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            # self.assertEqual(delete_response.status_code, 200)
            # self.assertIn("message", delete_response.get_json())

            options_id_response = self.client.options("/api/v1/landing/1", headers=self.headers)
            logger.debug("OPTIONS Response: %s, Content: %s", options_id_response.status_code, options_id_response.data)
            self.assertEqual(options_id_response.status_code, 200)
            self.assertIn("message", options_id_response.get_json())

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_landing_route: %s", e)
            self.fail(f"test_landing_route failed: {e}")


if __name__ == "__main__":
    unittest.main()
