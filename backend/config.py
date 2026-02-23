import os
from pathlib import Path
from dotenv import load_dotenv

# backend/config.py の 2 階層上がプロジェクトルート (ConnectAIOEMSample/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(_PROJECT_ROOT / "backend" / ".env")


def _resolve_path(raw: str) -> str:
    """相対パスをプロジェクトルート基準の絶対パスに変換する。"""
    p = Path(raw)
    return str(p if p.is_absolute() else _PROJECT_ROOT / p)


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL", "sqlite:///datahub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    CONNECT_AI_BASE_URL: str = os.environ.get("CONNECT_AI_BASE_URL", "https://cloud.cdata.com/api")
    CONNECT_AI_PARENT_ACCOUNT_ID: str = os.environ.get("CONNECT_AI_PARENT_ACCOUNT_ID", "")
    CONNECT_AI_PRIVATE_KEY: str = os.environ.get("CONNECT_AI_PRIVATE_KEY", "")
    CONNECT_AI_PRIVATE_KEY_PATH: str = _resolve_path(
        os.environ.get("CONNECT_AI_PRIVATE_KEY_PATH", "backend/keys/private.key")
    )
    APP_BASE_URL: str = os.environ.get("APP_BASE_URL", "http://localhost:5001")
