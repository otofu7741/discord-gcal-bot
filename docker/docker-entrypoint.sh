#!/bin/bash

# Discord Calendar Bot - Docker起動スクリプト

set -e

echo "🐳 Discord Calendar Bot - Docker版"
echo "=================================="

# 環境変数チェック
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ 環境変数 $1 が設定されていません"
        return 1
    else
        echo "✅ $1: 設定済み"
        return 0
    fi
}

echo "📋 環境変数チェック..."
check_env_var "DISCORD_TOKEN"
check_env_var "GOOGLE_SERVICE_ACCOUNT_PATH"
check_env_var "GOOGLE_CALENDAR_ID"

# サービスアカウントキーファイルの確認
SERVICE_ACCOUNT_PATH="${GOOGLE_SERVICE_ACCOUNT_PATH:-credentials/service-account-key.json}"
if [ ! -f "$SERVICE_ACCOUNT_PATH" ]; then
    echo "❌ サービスアカウントキーファイルが見つかりません: $SERVICE_ACCOUNT_PATH"
    echo "💡 確認事項:"
    echo "   - credentials/service-account-key.json が存在するか"
    echo "   - docker-compose.yml でボリュームマウントが正しく設定されているか"
    exit 1
else
    echo "✅ サービスアカウントキー: $SERVICE_ACCOUNT_PATH"
fi

echo "=================================="
echo "🚀 Discord Calendar Bot を起動します..."
echo "=================================="

# Pythonアプリケーションを実行
exec python src/main.py
