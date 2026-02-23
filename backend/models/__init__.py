from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .api_log import ApiLog  # noqa: E402, F401
