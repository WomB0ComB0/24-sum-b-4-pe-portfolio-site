from peewee import Model, CharField, TextField, DateTimeField, SQL, PrimaryKeyField
from portfolio.db import mydb


class BaseModel(Model):
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(
        constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")]
    )

    class Meta:
        database = mydb


class Hobbies(BaseModel):
    hobbies_id = PrimaryKeyField()
    name = CharField()
    description = TextField()
    image = CharField()


class Projects(BaseModel):
    projects_id = PrimaryKeyField()
    name = CharField()
    description = TextField()
    url = CharField()
    language = CharField()


class Timeline(BaseModel):
    timeline_id = PrimaryKeyField()
    title = CharField()
    description = TextField()
    date = DateTimeField()
