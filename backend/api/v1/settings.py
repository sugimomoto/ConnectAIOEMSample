from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from backend.api.v1 import api_v1_bp
from backend.models import db
from backend.services import crypto_service


# --- ページルーティング ---

@api_v1_bp.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html")


# --- API ---

@api_v1_bp.route("/api/v1/settings/api-key", methods=["POST"])
@login_required
def save_api_key():
    data = request.get_json()
    api_key = (data or {}).get("api_key", "").strip()

    if not api_key:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "API Key を入力してください"}}), 400

    if not api_key.startswith("sk-ant-"):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "有効な Claude API Key を入力してください（sk-ant- から始まる形式）"}}), 400

    try:
        current_user.claude_api_key_encrypted = crypto_service.encrypt(api_key)
    except RuntimeError as e:
        return jsonify({"error": {"code": "SERVER_MISCONFIGURATION", "message": str(e)}}), 500

    db.session.commit()

    return jsonify({"message": "API Key を保存しました"}), 200


@api_v1_bp.route("/api/v1/settings/api-key", methods=["DELETE"])
@login_required
def delete_api_key():
    current_user.claude_api_key_encrypted = None
    db.session.commit()
    return jsonify({"message": "API Key を削除しました"}), 200


@api_v1_bp.route("/api/v1/settings/api-key/status", methods=["GET"])
@login_required
def get_api_key_status():
    has_key = current_user.claude_api_key_encrypted is not None
    return jsonify({"has_api_key": has_key}), 200
