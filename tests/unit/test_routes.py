import unittest
import os
from flask import g
from portfolio import create_app
from portfolio.mysql_db import Projects, Hobbies, Timeline
from dotenv import load_dotenv
import requests_mock
from peewee import MySQLDatabase

load_dotenv()

os.environ["FLASK_APP"] = "main"
root_path = os.path.dirname(os.path.abspath(__file__))

# Assuming you have a function to create your Flask app
app = create_app()

# Database configuration
mydb = MySQLDatabase(
    os.getenv('MYSQL_DATABASE'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    host=os.getenv('MYSQL_HOST'),
    port=3306
)

class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mydb.connect()
        mydb.create_tables([Hobbies, Projects, Timeline])
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        mydb.drop_tables([Hobbies, Projects, Timeline])
        mydb.close()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Home', response.data)

    def test_hobbies_route(self):
        response = self.client.get('/hobbies', headers={"Authorization": f'{os.getenv("TOKEN")}'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hobbies', response.data)

    @requests_mock.Mocker()
    def test_projects_route(self, mocker):
        mocker.get('http://localhost/api/v1/projects', json={"projects": []})
        response = self.client.get('/projects', headers={"Authorization": f'{os.getenv("TOKEN")}'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Projects', response.data)

    def test_contact_get_route(self):
        response = self.client.get('/contact')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Contact', response.data)

    def test_contact_post_route(self):
        response = self.client.post('/contact', data={
            "name": "John Doe",
            "profession": "Developer",
            "company": "Tech Inc.",
            "email": "john@example.com",
            "subject": "Hello",
            "message": "This is a test message."
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Form submitted successfully', response.data)

    @requests_mock.Mocker()
    def test_api_projects_get_route(self, mocker):
        mocker.get(
            'http://localhost:5000/api/v1/projects',
            json={"projects": []},
            request_headers={"Authorization": f'{os.getenv("TOKEN")}'}
        )
        response = self.client.get(
            '/api/v1/projects', headers={"Authorization": f'{os.getenv("TOKEN")}'}
        )
        self.assertEqual(response.status_code, 200)

    @requests_mock.Mocker()
    def test_api_hobbies_get_route(self, mocker):
        mocker.get(
            'http://localhost:5000/api/v1/hobbies',
            json={"hobbies": []},
            request_headers={"Authorization": f'{os.getenv("TOKEN")}'}
        )
        response = self.client.get(
            '/api/v1/hobbies', headers={"Authorization": f'{os.getenv("TOKEN")}'}
        )
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()