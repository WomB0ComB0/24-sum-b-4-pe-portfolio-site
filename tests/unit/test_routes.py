import unittest
import os
import datetime
from peewee import MySQLDatabase, Model, CharField, TextField, DateTimeField
from portfolio import create_app
from dotenv import load_dotenv

load_dotenv()

# Initialize the database connection
mydb = MySQLDatabase(
    os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=3306,
)

class BaseModel(Model):
    class Meta:
        database = mydb

class Test_Hobbies(BaseModel):
    name = CharField()
    description = TextField()
    image = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

class Test_Projects(BaseModel):
    name = CharField()
    description = TextField()
    url = CharField()
    language = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

class Test_Timeline(BaseModel):
    title = CharField()
    description = TextField()
    date = DateTimeField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        mydb.connect()
        mydb.create_tables([Test_Hobbies, Test_Projects, Test_Timeline])

    @classmethod
    def tearDownClass(cls):
        mydb.drop_tables([Test_Hobbies, Test_Projects, Test_Timeline])
        mydb.close()

    def setUp(self):
        self.client = self.app.test_client()
        self.headers = {
            'Authorization': f"{os.getenv("TOKEN")}"
        }

    def test_hobbies_route(self):
        response = self.client.get('/api/v1/hobbies', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_projects_route(self):
        response = self.client.get('/api/v1/projects', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_timeline_route(self):
        response = self.client.get('/api/v1/timeline', headers=self.headers)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()