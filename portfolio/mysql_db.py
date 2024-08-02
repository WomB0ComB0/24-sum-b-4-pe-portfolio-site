from peewee import Model, CharField, TextField, DateTimeField, AutoField, SQL
from portfolio.db import mydb


class BaseModel(Model):
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(
        constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")]
    )

    class Meta:
        database = mydb


class Hobbies(BaseModel):
    hobbies_id = AutoField()
    name = CharField()
    description = TextField()
    image = CharField()


class Projects(BaseModel):
    projects_id = AutoField()
    name = CharField()
    description = TextField()
    url = CharField()
    language = CharField()


class Timeline(BaseModel):
    timeline_id = AutoField()
    title = CharField()
    description = TextField()
    date = DateTimeField()
