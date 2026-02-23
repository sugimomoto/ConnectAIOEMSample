#!/bin/bash
set -e

echo "=== ConnectAIOEMSample DevContainer セットアップ ==="

# 依存パッケージのインストール
echo "📦 pip install -r backend/requirements.txt ..."
pip install -r backend/requirements.txt

# .env が未作成の場合はテンプレートからコピー
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "✅ backend/.env を作成しました。必要な値を設定してください。"
else
  echo "ℹ️  backend/.env は既に存在します。スキップします。"
fi

# keys ディレクトリ作成
mkdir -p backend/keys

# DB マイグレーション
echo "🗄️  DB マイグレーションを実行します..."
PYTHONPATH=$(pwd) flask --app backend.app db upgrade

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "次のステップ:"
echo "  1. backend/.env を編集して以下を設定してください:"
echo "       CONNECT_AI_PARENT_ACCOUNT_ID=<your-parent-account-id>"
echo "       CONNECT_AI_PRIVATE_KEY=\"-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\""
echo "       SECRET_KEY=<random-string>"
echo ""
echo "  2. 開発サーバーを起動:"
echo "       flask --app backend.app run --port 5001 --debug"
echo ""
echo "  3. ブラウザで http://localhost:5001 にアクセス"
