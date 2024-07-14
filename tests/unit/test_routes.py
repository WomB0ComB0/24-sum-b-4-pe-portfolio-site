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
mydb = None

class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global mydb
        mydb = MySQLDatabase(
            os.getenv("TEST_MYSQL_DATABASE"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            host=os.getenv("MYSQL_HOST"),
            port=3306,
        )
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

    def setUp(self):
        Hobbies.create(
            name="Reading",
            description="Reading various books and articles.",
            image="https://example.com/images/reading.jpg",
        )
        Hobbies.create(
            name="Gardening",
            description="Growing and taking care of plants.",
            image="https://example.com/images/gardening.jpg",
        )
        Projects.create(
            name="Portfolio Website",
            description="A personal portfolio website.",
            url="https://example.com/portfolio",
            language="Python",
        )
        Projects.create(
            name="Weather App",
            description="An app to check the weather.",
            url="https://example.com/weather",
            language="JavaScript",
        )
        Timeline.create(
            title="Started Learning Python",
            description="Began learning Python programming language.",
            date="2020-01-01",
        )
        Timeline.create(
            title="Built First Website",
            description="Created my first personal website.",
            date="2021-06-15",
        )

    def tearDown(self):
        with mydb.atomic():
            Hobbies.delete().execute(mydb)
            Projects.delete().execute(mydb)
            Timeline.delete().execute(mydb)

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Home", response.data)

    @requests_mock.Mocker()
    def test_hobbies_route(self, mocker):
        mocker.get("http://localhost:5000/api/v1/hobbies", json={"hobbies": []})
        response = self.client.get(
            "http://localhost:5000/hobbies",
            headers={"Authorization": f'{os.getenv("TOKEN")}'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hobbies", response.data)

    @requests_mock.Mocker()
    def test_projects_route(self, mocker):
        mocker.get("http://localhost:5000/api/v1/projects", json={"projects": []})
        response = self.client.get(
            "http://localhost:5000/projects",
            headers={"Authorization": f'{os.getenv("TOKEN")}'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Projects", response.data)

    def test_contact_get_route(self):
        response = self.client.get("/contact")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()