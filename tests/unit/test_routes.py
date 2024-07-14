import unittest
import os
import time
from flask import g
from portfolio import create_app
from portfolio.mysql_db import Projects, Hobbies, Timeline
from dotenv import load_dotenv
import requests_mock
from peewee import MySQLDatabase
import subprocess

load_dotenv()

os.environ["FLASK_APP"] = "main"
root_path = os.path.dirname(os.path.abspath(__file__))

app = create_app()

mydb = MySQLDatabase(
    os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=3306,
)


class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Connecting to the database...")
        mydb.connect()
        print("Creating tables...")
        mydb.create_tables([Hobbies, Projects, Timeline])
        cls.client = app.test_client()

        print("Starting Flask server...")
        cls.flask_process = subprocess.Popen(
            ["flask", "run", "--host=0.0.0.0", "--port=5000"]
        )
        time.sleep(5)
    @classmethod
    def tearDownClass(cls):
        print("Dropping tables...")
        mydb.drop_tables([Hobbies, Projects, Timeline])
        print("Closing database connection...")
        mydb.close()

        print("Stopping Flask server...")
        cls.flask_process.terminate()
        cls.flask_process.wait()

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Home", response.data)

    @requests_mock.Mocker()
    def test_hobbies_route(self, mocker):
        mocker.get("http://0.0.0.0:5000/api/v1/hobbies", json={"hobbies": []})
        response = self.client.get(
            "/hobbies", headers={"Authorization": f'{os.getenv("TOKEN")}'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hobbies", response.data)

    @requests_mock.Mocker()
    def test_projects_route(self, mocker):
        mocker.get("http://0.0.0.0:5000/api/v1/projects", json={"projects": []})
        response = self.client.get(
            "/projects", headers={"Authorization": f'{os.getenv("TOKEN")}'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Projects", response.data)

    def test_contact_get_route(self):
        response = self.client.get("/contact")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()