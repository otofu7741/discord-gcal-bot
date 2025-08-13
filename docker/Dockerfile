# Python 3.13をベースイメージとして使用
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係ファイルをコピー
COPY pyproject.toml ./

# pipを最新版にアップグレード
RUN pip install --upgrade pip

# 依存関係をインストール
RUN pip install -e .

# アプリケーションのソースコードをコピー
COPY src/ ./src/
COPY docker/docker-entrypoint.sh ./

# エントリーポイントスクリプトに実行権限を付与
RUN chmod +x docker-entrypoint.sh

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash bot
RUN chown -R bot:bot /app
USER bot

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# アプリケーションを実行
CMD ["python", "main.py"]
