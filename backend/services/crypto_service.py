from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def encrypt(plaintext: str) -> str:
    """平文を Fernet 対称暗号で暗号化して返す。"""
    key = current_app.config["ENCRYPTION_KEY"]
    if not key:
        raise RuntimeError("ENCRYPTION_KEY が設定されていません")
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Fernet 暗号文を復号して返す。

    Raises:
        ValueError: キーが不正またはトークンが改ざんされている場合
    """
    key = current_app.config["ENCRYPTION_KEY"]
    if not key:
        raise RuntimeError("ENCRYPTION_KEY が設定されていません")
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise ValueError("復号に失敗しました") from e
