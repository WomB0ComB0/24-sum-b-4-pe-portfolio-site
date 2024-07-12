from functools import wraps
from flask import request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()


def check_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if auth != os.getenv("TOKEN"):
            return jsonify({"message": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated_function
