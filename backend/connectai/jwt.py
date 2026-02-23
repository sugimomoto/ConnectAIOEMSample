import time
import jwt
from cryptography.hazmat.primitives import serialization
from flask import current_app


def generate_connect_ai_jwt(parent_account_id: str, subject_account_id: str) -> str:
    """
    Connect AI API 用 RS256 JWT を生成する。

    Args:
        parent_account_id: ParentAccountId（iss クレーム）
        subject_account_id: 呼び出し対象アカウントID（sub クレーム）
                            子アカウント未作成時は空文字列にする

    Returns:
        署名済み JWT 文字列
    """
    private_key_path = current_app.config["CONNECT_AI_PRIVATE_KEY_PATH"]
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    now = int(time.time())
    payload = {
        "tokenType": "powered-by",
        "iss": parent_account_id,
        "sub": subject_account_id,
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")
