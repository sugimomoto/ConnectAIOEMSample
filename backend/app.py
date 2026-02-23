import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from backend.models import db

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(test_config: dict | None = None):
    app = Flask(
        __name__,
        static_folder=os.path.join(_BASE_DIR, "frontend", "static"),
        template_folder=os.path.join(_BASE_DIR, "frontend", "pages"),
    )
    app.config.from_object("backend.config.Config")

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = "api_v1.login_page"

    @login_manager.user_loader
    def load_user(user_id: str):
        from backend.models.user import User
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith("/api/"):
            return jsonify({"error": {"code": "UNAUTHORIZED"}}), 401
        return redirect(url_for("api_v1.login_page"))

    from backend.api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp)

    from backend.middleware.error_handler import register_error_handlers
    register_error_handlers(app)

    return app
