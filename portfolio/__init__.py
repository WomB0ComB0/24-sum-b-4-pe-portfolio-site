from flask import Flask
import os
import logging
from portfolio.db import mydb
from portfolio.mysql_db import (
    Hobbies,
    Projects,
    Timeline,
)
from peewee import DatabaseError


def create_app():
    """Construct the core application."""
    app = Flask(__name__, template_folder="templates")
    print(os.getenv("TEST"))
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    with app.app_context():
        from portfolio import routes

        try:
            mydb.connect()
            mydb.create_tables([Hobbies, Projects, Timeline])
            logger.info("Tables created successfully")
            mydb.close()
        except DatabaseError as e:
            logger.error("Database error: %s", e)
        return app
