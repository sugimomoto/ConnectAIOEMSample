from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from backend.api.v1 import api_v1_bp
from backend.services.auth_service import AuthService
from backend.schemas.user_schema import RegisterSchema, LoginSchema
from pydantic import ValidationError

auth_service = AuthService()


# --- ページルーティング ---

@api_v1_bp.route("/")
def index():
    return redirect(url_for("api_v1.dashboard_page"))


@api_v1_bp.route("/login")
def login_page():
    return render_template("login.html")


@api_v1_bp.route("/register")
def register_page():
    return render_template("register.html")


@api_v1_bp.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")


# --- API ---

@api_v1_bp.route("/api/v1/auth/register", methods=["POST"])
def register():
    try:
        schema = RegisterSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400

    try:
        user, warning = auth_service.register(schema.email, schema.password, schema.name)
    except ValueError as e:
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    resp: dict = {"user": {"id": user.id, "email": user.email, "name": user.name}}
    if warning:
        resp["warning"] = warning
    return jsonify(resp), 201


@api_v1_bp.route("/api/v1/auth/login", methods=["POST"])
def login():
    try:
        schema = LoginSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400

    try:
        user = auth_service.login(schema.email, schema.password)
    except ValueError as e:
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": str(e)}}), 401

    return jsonify({"user": {"id": user.id, "email": user.email, "name": user.name}}), 200


@api_v1_bp.route("/api/v1/auth/logout", methods=["POST"])
@login_required
def logout():
    auth_service.logout()
    return jsonify({"message": "ログアウトしました"}), 200


@api_v1_bp.route("/api/v1/auth/me", methods=["GET"])
@login_required
def me():
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "connect_ai_account_id": current_user.connect_ai_account_id,
        }
    }), 200
