from flask import jsonify, request, render_template
from flask_login import login_required
from backend.api.v1 import api_v1_bp
from backend.services.data_service import DataService
from backend.schemas.data_schema import (
    RecordListSchema,
    RecordWriteSchema,
    RecordUpdateSchema,
    RecordDeleteSchema,
)
from backend.connectai.exceptions import ConnectAIError
from pydantic import ValidationError

data_service = DataService()


# --- ページルーティング ---

@api_v1_bp.route("/data-browser")
@login_required
def data_browser_page():
    return render_template("data-browser.html")


# --- API ---

@api_v1_bp.route("/api/v1/data/records", methods=["GET"])
@login_required
def get_records():
    try:
        req = RecordListSchema(**request.args.to_dict())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400
    try:
        result = data_service.list_records(req)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify(result), 200


@api_v1_bp.route("/api/v1/data/records", methods=["POST"])
@login_required
def create_record():
    try:
        req = RecordWriteSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400
    try:
        result = data_service.create_record(req)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify(result), 201


@api_v1_bp.route("/api/v1/data/records", methods=["PUT"])
@login_required
def update_record():
    try:
        req = RecordUpdateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400
    try:
        result = data_service.update_record(req)
    except ValueError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify(result), 200


@api_v1_bp.route("/api/v1/data/records", methods=["DELETE"])
@login_required
def delete_record():
    try:
        req = RecordDeleteSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400
    try:
        result = data_service.delete_record(req)
    except ValueError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify(result), 200
