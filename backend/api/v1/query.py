from flask import jsonify, request, render_template
from flask_login import login_required
from backend.api.v1 import api_v1_bp
from backend.services.query_service import QueryService
from backend.schemas.query_schema import QueryRequestSchema
from backend.connectai.exceptions import ConnectAIError
from pydantic import ValidationError

query_service = QueryService()


# --- ページルーティング ---

@api_v1_bp.route("/query")
@login_required
def query_page():
    return render_template("query.html")


# --- API ---

@api_v1_bp.route("/api/v1/query", methods=["POST"])
@login_required
def execute_query():
    try:
        req = QueryRequestSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400
    try:
        result = query_service.execute_query(req)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify(result), 200
