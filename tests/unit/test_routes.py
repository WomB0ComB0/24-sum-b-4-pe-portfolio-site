import unittest
import os
import datetime
import importlib.metadata
import logging
from peewee import MySQLDatabase, Model, CharField, TextField, DateTimeField, DatabaseError
from portfolio import create_app
from dotenv import load_dotenv
import requests

werzeug_version = importlib.metadata.version("werkzeug")
load_dotenv()

mydb = MySQLDatabase(
    os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=3306,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BaseModel(Model):
    class Meta:
        database = mydb

class HobbiesModel(BaseModel):
    name = CharField()
    description = TextField()
    image = CharField()

class ProjectsModel(BaseModel):
    name = CharField()
    description = TextField()
    url = CharField()
    language = CharField()

class TimelineModel(BaseModel):
    title = CharField()
    description = TextField()
    date = DateTimeField()

class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            logger.debug("Setting up class")
            cls.app = create_app()
            cls.client = cls.app.test_client()
            try:
                mydb.connect()
                mydb.create_tables([HobbiesModel, ProjectsModel, TimelineModel])
            except DatabaseError as e:
                logger.error("Database error in setUpClass: %s", e)
                raise e
            except Exception as e:
                logger.error("Unexpected error in setUpClass: %s", e)
                raise e
        except Exception as e:
            logger.error("Error in setUpClass: %s", e)
            raise e

    @classmethod
    def tearDownClass(cls):
        mydb.drop_tables([HobbiesModel, ProjectsModel, TimelineModel])
        mydb.close()

    def setUp(self):
        self.client = self.app.test_client()
        self.headers = {
            'Authorization': os.getenv("TOKEN"),
            'HTTP_USER_AGENT': f"werkzeug/{werzeug_version}"
        }

    def test_hobbies_route(self):
        try:
            get_response = self.client.get('/api/v1/hobbies', headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)
            post_response = self.client.post('/api/v1/hobbies', headers=self.headers, json={
                "name": "Test",
                "description": "Test",
                "image": "Test"
            }, content_type='application/json')
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)
            delete_response = self.client.delete('/api/v1/hobbies', headers=self.headers, json={
                "id": 1
            }, content_type='application/json')
            logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            self.assertEqual(delete_response.status_code, 200)
        except requests.exceptions.RequestException as e:
            logger.error("Error in test_hobbies_route: %s", e)
            self.fail(f"test_hobbies_route failed: {e}")

    def test_projects_route(self):
        try:
            get_response = self.client.get('/api/v1/projects', headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)
            post_response = self.client.post('/api/v1/projects', headers=self.headers, json={
                "name": "Test",
                "description": "Test",
                "url": "Test",
                "language": "Test"
            }, content_type='application/json')
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)
            delete_response = self.client.delete('/api/v1/projects', headers=self.headers, json={
                "name": "Test"
            }, content_type='application/json')
            logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            self.assertEqual(delete_response.status_code, 200)
        except requests.exceptions.RequestException as e:
            logger.error("Error in test_projects_route: %s", e)
            self.fail(f"test_projects_route failed: {e}")

    def test_timeline_route(self):
        try:
            get_response = self.client.get('/api/v1/timeline', headers=self.headers)
            logger.debug("GET Response: %s, Content: %s", get_response.status_code, get_response.data)
            self.assertEqual(get_response.status_code, 200)
            post_response = self.client.post('/api/v1/timeline', headers=self.headers, json={
                "title": "Test",
                "description": "Test",
                "date": "2021-01-01"
            }, content_type='application/json')
            logger.debug("POST Response: %s, Content: %s", post_response.status_code, post_response.data)
            self.assertEqual(post_response.status_code, 200)
            delete_response = self.client.delete('/api/v1/timeline', headers=self.headers, json={
                "title": "Test"
            }, content_type='application/json')
            logger.debug("DELETE Response: %s, Content: %s", delete_response.status_code, delete_response.data)
            self.assertEqual(delete_response.status_code, 200)
        except requests.exceptions.RequestException as e:
            logger.error("Error in test_timeline_route: %s", e)
            self.fail(f"test_timeline_route failed: {e}")

if __name__ == '__main__':
    unittest.main()