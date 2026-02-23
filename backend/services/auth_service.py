import bcrypt
from flask_login import login_user, logout_user
from backend.models import db
from backend.models.user import User
from backend.connectai.client import ConnectAIClient
from backend.connectai.exceptions import ConnectAIError


class AuthService:

    def register(self, email: str, password: str, name: str) -> tuple[User, str | None]:
        """
        ユーザー登録。Connect AI 子アカウントの作成も行う。

        Returns:
            (User, error_message)
            Connect AI API 失敗時は User を返しつつ error_message に詳細を返す

        Raises:
            ValueError: メールアドレスが重複している場合
        """
        if User.query.filter_by(email=email).first():
            raise ValueError("このメールアドレスはすでに登録されています")

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()

        user = User(email=email, password_hash=password_hash, name=name)
        db.session.add(user)
        db.session.commit()

        error_msg = None
        try:
            client = ConnectAIClient(child_account_id=None)
            child_account_id = client.create_account(str(user.id))
            user.connect_ai_account_id = child_account_id
            db.session.commit()
        except ConnectAIError as e:
            error_msg = f"アカウント作成は完了しましたが、Connect AI連携に失敗しました: {e}"

        login_user(user)
        return user, error_msg

    def login(self, email: str, password: str) -> User:
        """
        メール・パスワードを検証してセッションを開始する。

        Raises:
            ValueError: 認証失敗
        """
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("メールアドレスまたはパスワードが正しくありません")

        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise ValueError("メールアドレスまたはパスワードが正しくありません")

        login_user(user)
        return user

    def logout(self) -> None:
        logout_user()
