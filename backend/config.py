import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL", "sqlite:///datahub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    CONNECT_AI_BASE_URL: str = os.environ.get("CONNECT_AI_BASE_URL", "https://cloud.cdata.com/api")
    CONNECT_AI_PARENT_ACCOUNT_ID: str = os.environ.get("CONNECT_AI_PARENT_ACCOUNT_ID", "")
    CONNECT_AI_PRIVATE_KEY_PATH: str = os.environ.get("CONNECT_AI_PRIVATE_KEY_PATH", "backend/keys/private.key")
    APP_BASE_URL: str = os.environ.get("APP_BASE_URL", "http://localhost:5001")
