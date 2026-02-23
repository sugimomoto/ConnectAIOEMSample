from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # ChildAccountId: ユーザー登録時に Connect AI から発行される子アカウントID
    connect_ai_account_id = db.Column(db.String(255), nullable=True)
    # Claude API Key（Fernet 対称暗号で暗号化して保存）
    claude_api_key_encrypted = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
