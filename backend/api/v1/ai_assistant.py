from flask import render_template, request, jsonify, session, current_app
from flask_login import login_required, current_user
from backend.api.v1 import api_v1_bp
from backend.services import crypto_service
from backend.services import claude_service
from backend.connectai.jwt import generate_connect_ai_jwt


# --- ページルーティング ---

@api_v1_bp.route("/ai-assistant")
@login_required
def ai_assistant_page():
    return render_template("ai_assistant.html")


# --- API ---

@api_v1_bp.route("/api/v1/ai-assistant/chat", methods=["POST"])
@login_required
def ai_assistant_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    catalog_name = data.get("catalog_name", "").strip() or None

    if not message:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "メッセージを入力してください"}}), 400

    if not current_user.claude_api_key_encrypted:
        return jsonify({
            "error": {
                "code": "NO_API_KEY",
                "message": "Claude API Key が設定されていません。設定画面から登録してください。",
            }
        }), 422

    try:
        api_key = crypto_service.decrypt(current_user.claude_api_key_encrypted)
    except (RuntimeError, ValueError) as e:
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500

    account_id = current_user.connect_ai_account_id
    if not account_id:
        return jsonify({
            "error": {"code": "NO_ACCOUNT", "message": "Connect AI アカウントが設定されていません"}
        }), 422

    parent_id = current_app.config["CONNECT_AI_PARENT_ACCOUNT_ID"]
    jwt_token = generate_connect_ai_jwt(parent_id, account_id)

    history: list[dict] = session.get("chat_history", [])
    history.append({"role": "user", "content": message})

    try:
        answer, tool_calls = claude_service.chat(api_key, jwt_token, history, catalog_name)
    except Exception as e:
        return jsonify({"error": {"code": "CLAUDE_ERROR", "message": str(e)}}), 500

    history.append({"role": "assistant", "content": answer})
    session["chat_history"] = history

    return jsonify({"answer": answer, "tool_calls": tool_calls}), 200


@api_v1_bp.route("/api/v1/ai-assistant/reset", methods=["POST"])
@login_required
def ai_assistant_reset():
    session.pop("chat_history", None)
    return jsonify({"message": "会話をリセットしました"}), 200
