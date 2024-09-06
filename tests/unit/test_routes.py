import sys
import os
import unittest
import importlib.metadata
import logging
from flask import g
import sqlite3
from typing import Dict, Any, List

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

    def test_regular(self) -> None:
        self._test_regular(
            "hobbies",
            {
                "id": 1,
                "name": "Test Hobby",
                "description": "Test Description",
                "image": "test.jpg",
            },
        )
        self._test_regular(
            "projects",
            {
                "id": 1,
                "name": "Test Project",
                "description": "Test Description",
                "url": "test.com",
                "language": "Python",
            },
        )
        self._test_regular(
            "timeline",
            {
                "id": 1,
                "title": "Test Event",
                "description": "Test Description",
                "date": "2023-01-01",
            },
        )

    def _test_regular(self, name: str, body: Any) -> None:
        try:
            logger.debug(f"Starting test_{name}_route")
            if body:
                post_response = self.client.post(
                    f"/api/v1/{name}",
                    headers=self.headers,
                    json=body,
                    content_type="application/json",
                )
                logger.debug(
                    f"POST Response: {post_response.status_code}, Content: {post_response.data}"
                )
                if post_response.status_code != 201:
                    logger.error(
                        f"POST failed with status {post_response.status_code}: {post_response.data}"
                    )
                self.assertEqual(post_response.status_code, 201)
            get_response = self.client.get(f"/api/v1/{name}", headers=self.headers)
            logger.debug(
                f"GET Response: {get_response.status_code}, Content: {get_response.data}"
            )
            self.assertEqual(get_response.status_code, 200)
            if body:
                delete_response = self.client.delete(
                    f"/api/v1/{name}/{body['id']}",
                    headers=self.headers,
                )
                logger.debug(
                    f"DELETE Response: {delete_response.status_code}, Content: {delete_response.data}"
                )
                self.assertEqual(delete_response.status_code, 200)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_regular: {e}")
            self.fail(f"test_regular failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in test_regular: {e}")
            logger.error(f"Request body: {body}")
            self.fail(f"test_regular failed unexpectedly: {e}")

    def test_hobbies_route(self) -> None:
        try:
            logger.debug("Starting test_hobbies_route")

            get_response = self.client.get("/api/v1/hobbies", headers=self.headers)
            logger.debug(
                f"GET Response: {get_response.status_code}, Content: {get_response.data}"
            )
            self.assertEqual(get_response.status_code, 200)

            post_data = {
                "hobbies_id": 1,
                "name": "Test",
                "description": "Test",
                "image": "Test",
            }
            post_response = self.client.post(
                "/api/v1/hobbies",
                headers=self.headers,
                json=post_data,
                content_type="application/json",
            )
            logger.debug(
                f"POST Response: {post_response.status_code}, Content: {post_response.data}"
            )
            self.assertEqual(post_response.status_code, 201)

            get_after_post = self.client.get("/api/v1/hobbies", headers=self.headers)
            logger.debug(
                f"GET Response: {get_after_post.status_code}, Content: {get_after_post.data}"
            )
            hobbies = get_after_post.get_json()
            if hobbies is None or (isinstance(hobbies, str) and hobbies == "[]"):
                self.fail("No hobbies found after POST")
            if isinstance(hobbies, str):
                hobbies = json.loads(hobbies)
            hobby_id = hobbies[0]["hobbies_id"]

            delete_response = self.client.delete(
                f"/api/v1/hobbies/{hobby_id}",
                headers=self.headers,
            )
            logger.debug(
                f"DELETE Response: {delete_response.status_code}, Content: {delete_response.data}"
            )
            self.assertEqual(delete_response.status_code, 200)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_hobbies_route: {e}")
            self.fail(f"test_hobbies_route failed: {e}")

    def test_projects_route(self) -> None:
        try:
            logger.debug("Starting test_projects_route")

            get_response = self.client.get("/api/v1/projects", headers=self.headers)
            logger.debug(
                f"GET Response: {get_response.status_code}, Content: {get_response.data}"
            )
            self.assertEqual(get_response.status_code, 200)

            post_data = {
                "projects_id": 1,
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
            logger.debug(
                f"POST Response: {post_response.status_code}, Content: {post_response.data}"
            )
            self.assertEqual(post_response.status_code, 201)

            get_after_post = self.client.get("/api/v1/projects", headers=self.headers)
            logger.debug(
                f"GET Response: {get_after_post.status_code}, Content: {get_after_post.data}"
            )
            projects = get_after_post.get_json()
            if projects is None or (isinstance(projects, str) and projects == "[]"):
                self.fail("No projects found after POST")
            if isinstance(projects, str):
                projects = json.loads(projects)
            project_id = projects[0]["projects_id"]

            delete_response = self.client.delete(
                f"/api/v1/projects/{project_id}",
                headers=self.headers,
            )
            logger.debug(
                f"DELETE Response: {delete_response.status_code}, Content: {delete_response.data}"
            )
            self.assertEqual(delete_response.status_code, 200)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_projects_route: {e}")
            self.fail(f"test_projects_route failed: {e}")

    def test_timeline_route(self) -> None:
        try:
            logger.debug("Starting test_timeline_route")

            get_response = self.client.get("/api/v1/timeline", headers=self.headers)
            logger.debug(
                f"GET Response: {get_response.status_code}, Content: {get_response.data}"
            )
            self.assertEqual(get_response.status_code, 200)

            post_data = {
                "timeline_id": 1,
                "title": "Test",
                "description": "Test",
                "date": "2021-01-01",
            }
            post_response = self.client.post(
                "/api/v1/timeline",
                headers=self.headers,
                json=post_data,
                content_type="application/json",
            )
            logger.debug(
                f"POST Response: {post_response.status_code}, Content: {post_response.data}"
            )
            self.assertEqual(post_response.status_code, 201)

            get_after_post = self.client.get("/api/v1/timeline", headers=self.headers)
            logger.debug(
                f"GET Response: {get_after_post.status_code}, Content: {get_after_post.data}"
            )
            timeline_items = get_after_post.get_json()
            if timeline_items is None or (
                isinstance(timeline_items, str) and timeline_items == "[]"
            ):
                self.fail("No timeline items found after POST")
            if isinstance(timeline_items, str):
                timeline_items = json.loads(timeline_items)
            timeline_id = timeline_items[0]["timeline_id"]

            delete_response = self.client.delete(
                f"/api/v1/timeline/{timeline_id}",
                headers=self.headers,
            )
            logger.debug(
                f"DELETE Response: {delete_response.status_code}, Content: {delete_response.data}"
            )
            self.assertEqual(delete_response.status_code, 200)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_timeline_route: {e}")
            self.fail(f"test_timeline_route failed: {e}")

    def test_projects_range_deletion(self) -> None:
        try:
            logger.debug("Starting test_projects_range_deletion")
            post_data_list = [
                {
                    "projects_id": 1,
                    "name": "Project 1",
                    "description": "Description 1",
                    "url": "url1",
                    "language": "Python",
                },
                {
                    "projects_id": 2,
                    "name": "Project 2",
                    "description": "Description 2",
                    "url": "url2",
                    "language": "JavaScript",
                },
                {
                    "projects_id": 3,
                    "name": "Project 3",
                    "description": "Description 3",
                    "url": "url3",
                    "language": "Java",
                },
            ]
            for post_data in post_data_list:
                post_response = self.client.post(
                    "/api/v1/projects", json=post_data, headers=self.headers
                )
                logger.debug(
                    f"POST Response: {post_response.status_code}, Content: {post_response.data}"
                )
                self.assertEqual(post_response.status_code, 201)

            delete_response = self.client.delete(
                "/api/v1/projects?start=1&end=3", headers=self.headers
            )
            logger.debug(
                f"DELETE Response: {delete_response.status_code}, Content: {delete_response.data}"
            )
            self.assertEqual(delete_response.status_code, 200)
            response_data = delete_response.get_json()
            if response_data is None:
                response_data = delete_response.data.decode("utf-8")
            logger.debug(f"Response data: {response_data}")
            self.assertIn("3 items deleted successfully", str(response_data))

            get_response = self.client.get("/api/v1/projects", headers=self.headers)
            logger.debug(
                f"GET Response: {get_response.status_code}, Content: {get_response.data}"
            )
            self.assertEqual(get_response.status_code, 200)
            projects = get_response.get_json()
            if projects is None:
                projects = get_response.data.decode("utf-8")
            logger.debug(f"Projects: {projects}")
            self.assertTrue(
                len(projects) == 0 or (isinstance(projects, str) and projects == "[]"),
                "Projects were not deleted as expected",
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_projects_range_deletion: {e}")
            self.fail(f"test_projects_range_deletion failed: {e}")

    def test_hobbies_range_deletion(self) -> None:
        try:
            logger.debug("Starting test_hobbies_range_deletion")
            post_data_list = [
                {
                    "hobbies_id": 1,
                    "name": "Hobby 1",
                    "description": "Description 1",
                    "image": "image1.jpg",
                },
                {
                    "hobbies_id": 2,
                    "name": "Hobby 2",
                    "description": "Description 2",
                    "image": "image2.jpg",
                },
                {
                    "hobbies_id": 3,
                    "name": "Hobby 3",
                    "description": "Description 3",
                    "image": "image3.jpg",
                },
            ]
            for post_data in post_data_list:
                post_response = self.client.post(
                    "/api/v1/hobbies", json=post_data, headers=self.headers
                )
                logger.debug(
                    f"POST Response: {post_response.status_code}, Content: {post_response.data}"
                )
                self.assertEqual(post_response.status_code, 201)

            delete_response = self.client.delete(
                "/api/v1/hobbies?start=1&end=3", headers=self.headers
            )
            logger.debug(
                f"DELETE Response: {delete_response.status_code}, Content: {delete_response.data}"
            )
            self.assertEqual(delete_response.status_code, 200)
            response_data = delete_response.get_json()
            if response_data is None:
                response_data = delete_response.data.decode("utf-8")
            logger.debug(f"Response data: {response_data}")
            self.assertIn("3 items deleted successfully", str(response_data))

            get_response = self.client.get("/api/v1/hobbies", headers=self.headers)
            logger.debug(
                f"GET Response: {get_response.status_code}, Content: {get_response.data}"
            )
            self.assertEqual(get_response.status_code, 200)
            hobbies = get_response.get_json()
            if hobbies is None:
                hobbies = get_response.data.decode("utf-8")
            logger.debug(f"Hobbies after deletion: {hobbies}")
            self.assertTrue(
                len(hobbies) == 0 or (isinstance(hobbies, str) and hobbies == "[]"),
                "Hobbies were not deleted as expected",
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_hobbies_range_deletion: {e}")
            self.fail(f"test_hobbies_range_deletion failed: {e}")

    def test_timeline_range_deletion(self) -> None:
        try:
            logger.debug("Starting test_timeline_range_deletion")
            post_data_list = [
                {
                    "timeline_id": 1,
                    "title": "Event 1",
                    "description": "Description 1",
                    "date": "2023-01-01",
                },
                {
                    "timeline_id": 2,
                    "title": "Event 2",
                    "description": "Description 2",
                    "date": "2023-02-01",
                },
                {
                    "timeline_id": 3,
                    "title": "Event 3",
                    "description": "Description 3",
                    "date": "2023-03-01",
                },
            ]
            for post_data in post_data_list:
                post_response = self.client.post(
                    "/api/v1/timeline", json=post_data, headers=self.headers
                )
                logger.debug(
                    f"POST Response: {post_response.status_code}, Content: {post_response.data}"
                )
                self.assertEqual(post_response.status_code, 201)

            delete_response = self.client.delete(
                "/api/v1/timeline?start=1&end=3", headers=self.headers
            )
            logger.debug(
                f"DELETE Response: {delete_response.status_code}, Content: {delete_response.data}"
            )
            self.assertEqual(delete_response.status_code, 200)
            response_data = delete_response.get_json()
            if response_data is None:
                response_data = delete_response.data.decode("utf-8")
            logger.debug(f"Response data: {response_data}")
            self.assertIn("3 items deleted successfully", str(response_data))

            get_response = self.client.get("/api/v1/timeline", headers=self.headers)
            logger.debug(
                f"GET Response: {get_response.status_code}, Content: {get_response.data}"
            )
            self.assertEqual(get_response.status_code, 200)
            timeline_items = get_response.get_json()
            if timeline_items is None:
                timeline_items = get_response.data.decode("utf-8")
            logger.debug(f"Timeline items after deletion: {timeline_items}")
            self.assertTrue(
                len(timeline_items) == 0
                or (isinstance(timeline_items, str) and timeline_items == "[]"),
                "Timeline items were not deleted as expected",
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in test_timeline_range_deletion: {e}")
            self.fail(f"test_timeline_range_deletion failed: {e}")

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
                response_data = get_response.get_json()
                if response_data is None:
                    response_data = get_response.data.decode("utf-8")
                self.assertIn("data", str(response_data))
                self.assertIn("metadata", str(response_data))
                logger.error("Response data: %s", response_data)
                logger.debug("Response data: %s", response_data)
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
                self.assertIn(
                    post_response.status_code,
                    [200, 201],
                    f"Unexpected status code: {post_response.status_code}",
                )
                response_data = post_response.get_json()
                if response_data is None:
                    response_data = post_response.data.decode("utf-8")
                self.assertIn("message", str(response_data))
                logger.error("Response data: %s", response_data)
                logger.debug("Response data: %s", response_data)
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
                response_data = options_response.get_json()
                if response_data is None:
                    response_data = options_response.data.decode("utf-8")
                self.assertIn("message", str(response_data))
                logger.error("Response data: %s", response_data)
                logger.debug("Response data: %s", response_data)
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
                response_data = get_id_response.get_json()
                if response_data is None:
                    response_data = get_id_response.data.decode("utf-8")
                self.assertIn("education", str(response_data))
                logger.error("Response data: %s", response_data)
                logger.debug("Response data: %s", response_data)
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
                response_data = put_response.get_json()
                if response_data is None:
                    response_data = put_response.data.decode("utf-8")
                self.assertIn("message", str(response_data))
                logger.debug("Response data: %s", response_data)
                logger.error("Response data: %s", response_data)
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
                response_data = delete_response.get_json()
                if response_data is None:
                    response_data = delete_response.data.decode("utf-8")
                self.assertIn("message", str(response_data))
                logger.error("Response data: %s", response_data)
                logger.debug("Response data: %s", response_data)
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
                response_data = options_id_response.get_json()
                if response_data is None:
                    response_data = options_id_response.data.decode("utf-8")
                self.assertIn("message", str(response_data))
            except Exception as e:
                logger.error("Error in test_landing_route: %s", e)
                self.fail(f"test_landing_route failed: {e}")

        except requests.exceptions.RequestException as e:
            logger.error("Error in test_landing_route: %s", e)
            self.fail(f"test_landing_route failed: {e}")


if __name__ == "__main__":
    unittest.main()
