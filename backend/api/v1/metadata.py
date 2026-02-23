from flask import jsonify, request, render_template
from flask_login import login_required
from backend.api.v1 import api_v1_bp
from backend.services.metadata_service import MetadataService
from backend.connectai.exceptions import ConnectAIError

metadata_service = MetadataService()


# --- ページルーティング ---

@api_v1_bp.route("/explorer")
@login_required
def explorer_page():
    return render_template("explorer.html")


# --- API ---

@api_v1_bp.route("/api/v1/metadata/catalogs", methods=["GET"])
@login_required
def get_catalogs():
    connection_id = request.args.get("connection_id")
    if not connection_id:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "connection_id は必須です"}}), 400
    try:
        catalogs = metadata_service.get_catalogs(connection_id)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"catalogs": catalogs}), 200


@api_v1_bp.route("/api/v1/metadata/schemas", methods=["GET"])
@login_required
def get_schemas():
    connection_id = request.args.get("connection_id")
    catalog_name = request.args.get("catalog_name")
    if not connection_id or not catalog_name:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "connection_id と catalog_name は必須です"}}), 400
    try:
        schemas = metadata_service.get_schemas(connection_id, catalog_name)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"schemas": schemas}), 200


@api_v1_bp.route("/api/v1/metadata/tables", methods=["GET"])
@login_required
def get_tables():
    connection_id = request.args.get("connection_id")
    catalog_name = request.args.get("catalog_name")
    schema_name = request.args.get("schema_name")
    if not connection_id or not catalog_name or not schema_name:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "connection_id / catalog_name / schema_name は必須です"}}), 400
    try:
        tables = metadata_service.get_tables(connection_id, catalog_name, schema_name)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"tables": tables}), 200


@api_v1_bp.route("/api/v1/metadata/columns", methods=["GET"])
@login_required
def get_columns():
    connection_id = request.args.get("connection_id")
    catalog_name = request.args.get("catalog_name")
    schema_name = request.args.get("schema_name")
    table_name = request.args.get("table_name")
    if not connection_id or not catalog_name or not schema_name or not table_name:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "connection_id / catalog_name / schema_name / table_name は必須です"}}), 400
    try:
        columns = metadata_service.get_columns(connection_id, catalog_name, schema_name, table_name)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"columns": columns}), 200
