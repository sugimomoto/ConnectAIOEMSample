from flask import jsonify, request, render_template
from flask_login import login_required
from backend.api.v1 import api_v1_bp
from backend.services.connection_service import ConnectionService
from backend.schemas.connection_schema import CreateConnectionSchema
from backend.connectai.exceptions import ConnectAIError
from pydantic import ValidationError

connection_service = ConnectionService()


# --- ページルーティング ---

@api_v1_bp.route("/connections")
@login_required
def connections_page():
    return render_template("connections.html")


@api_v1_bp.route("/connections/new")
@login_required
def connections_new_page():
    return render_template("connections-new.html")


@api_v1_bp.route("/callback")
@login_required
def callback_page():
    return render_template("callback.html")


# --- API ---

@api_v1_bp.route("/api/v1/datasources", methods=["GET"])
@login_required
def get_datasources():
    try:
        datasources = connection_service.get_datasources()
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"datasources": datasources}), 200


@api_v1_bp.route("/api/v1/connections", methods=["GET"])
@login_required
def get_connections():
    try:
        connections = connection_service.get_connections()
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"connections": connections}), 200


@api_v1_bp.route("/api/v1/connections", methods=["POST"])
@login_required
def create_connection():
    try:
        schema = CreateConnectionSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400

    try:
        redirect_url = connection_service.create_connection(schema.name, schema.data_source)
    except ValueError as e:
        return jsonify({"error": {"code": "FORBIDDEN", "message": str(e)}}), 403
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502

    return jsonify({"redirectURL": redirect_url}), 201


@api_v1_bp.route("/api/v1/connections/<connection_id>", methods=["DELETE"])
@login_required
def delete_connection(connection_id: str):
    try:
        connection_service.delete_connection(connection_id)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"message": "削除しました"}), 200
