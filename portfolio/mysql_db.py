from peewee import (
    Model,
    CharField,
    TextField,
    DateTimeField,
    SQL,
    AutoField,
    IntegerField,
)
from portfolio.db import mydb


class BaseModel(Model):
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(
        constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")]
    )

    class Meta:
        database = mydb


class Hobbies(BaseModel):
    id = AutoField(primary_key=True)
    hobbies_id = IntegerField(unique=True)  # Change this line
    name = CharField()
    description = TextField()
    image = CharField()


class Projects(BaseModel):
    id = AutoField(primary_key=True)
    projects_id = IntegerField(unique=True)  # Change this line
    name = CharField()
    description = TextField()
    url = CharField()
    language = CharField()


class Timeline(Model):
    id = AutoField(primary_key=True)
    timeline_id = IntegerField(unique=True)
    title = CharField()
    description = TextField()
    date = DateTimeField()

    class Meta:
        database = mydb
