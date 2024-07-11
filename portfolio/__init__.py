from flask import Flask
import logging
from portfolio.db import mydb
from portfolio.mysql_db import Hobbies, Projects
from peewee import DatabaseError

def create_app():
    """Construct the core application."""
    app = Flask(__name__, template_folder="templates")

    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    with app.app_context():
        from portfolio import routes
        try:
            mydb.connect()
            mydb.create_tables([Hobbies, Projects])
            logger.info("Tables created successfully")
            mydb.close()
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
        return app