from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from backend.api.v1 import api_v1_bp
from backend.services.api_log_service import ApiLogService

api_log_service = ApiLogService()


# --- ページルーティング ---

@api_v1_bp.route("/api-log")
@login_required
def api_log_page():
    return render_template("api-log.html")


# --- API ---

@api_v1_bp.route("/api/v1/api-logs", methods=["GET"])
@login_required
def get_api_logs():
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))
    result = api_log_service.list_logs(current_user.id, limit, offset)
    return jsonify(result), 200


@api_v1_bp.route("/api/v1/api-logs", methods=["DELETE"])
@login_required
def clear_api_logs():
    api_log_service.clear_logs(current_user.id)
    return jsonify({"message": "ログをクリアしました"}), 200
