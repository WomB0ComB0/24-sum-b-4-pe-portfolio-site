from peewee import Model, CharField, TextField, DateTimeField
import datetime
from portfolio.db import mydb

class Hobbies(Model):
    name = CharField()
    description = TextField()
    image = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
      database = mydb
      
class Projects(Model):
    name = CharField()
    description = TextField()
    url = CharField()
    language = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
      database = mydb

class Timeline(Model):
    title = CharField()
    description = TextField()
    date = DateTimeField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
      database = mydb
