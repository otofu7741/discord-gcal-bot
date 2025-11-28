#!/usr/bin/env python3
"""
Discord Calendar Bot セットアップスクリプト

このスクリプトは、Discord Calendar Bot の初期設定を行います。
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def ensure_directory(dir_path):
    """ディレクトリが存在しない場合は作成する"""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def check_file_exists(file_path):
    """ファイルの存在確認"""
    return Path(file_path).exists()


def parse_existing_env(env_file_path):
    """既存の.envファイルから設定を読み込む"""
    config = {}
    try:
        with open(env_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
    return config


def setup_discord_bot():
    """Discord Bot の設定"""
    print("\n🤖 Discord Bot 設定")
    print("-" * 30)

    print("Discord Bot の設定には以下が必要です:")
    print("1. Discord Developer Portal でアプリケーションを作成")
    print("2. Bot ユーザーを追加してトークンを取得")
    print("3. 必要な権限を設定してサーバーに招待")
    print()
    print("詳細な手順は README.md を参照してください。")
    print()

    token = input("Discord Bot Token を入力してください: ").strip()
    if not token:
        print("❌ Bot Token が入力されませんでした")
        return None

    return token


def setup_google_calendar():
    """Google Calendar API の設定"""
    print("\n📅 Google Calendar API 設定")
    print("-" * 30)

    print("Google Calendar API の設定には以下が必要です:")
    print("1. Google Cloud Console でプロジェクトを作成")
    print("2. Calendar API を有効化")
    print("3. サービスアカウントを作成してJSON キーをダウンロード")
    print("4. カレンダーをサービスアカウントと共有")
    print()
    print("詳細な手順は README.md を参照してください。")
    print()

    # サービスアカウントファイルの設定
    print("サービスアカウント JSON ファイルの設定:")
    print("- credentials/ ディレクトリに配置することを推奨")

    while True:
        service_file = input("サービスアカウント JSON ファイルのパス: ").strip()
        if not service_file:
            print("❌ ファイルパスが入力されませんでした")
            continue

        # 相対パスの場合は絶対パスに変換
        service_file_path = Path(service_file)
        if not service_file_path.is_absolute():
            service_file_path = Path.cwd() / service_file

        if not service_file_path.exists():
            print(f"❌ ファイルが見つかりません: {service_file_path}")
            print("ファイルパスを確認してください。")
            continue

        break

    # カレンダーIDの設定
    print()
    print("カレンダーID の設定:")
    print("  1. Google Calendar で対象カレンダーの設定を開く")
    print("  2. カレンダーIDをコピー（例: abc123@group.calendar.google.com）")
    print()

    calendar_id = input("使用するカレンダーID (デフォルト: primary): ").strip()
    if not calendar_id:
        calendar_id = "primary"

    return {"service_account_file": str(service_file_path), "calendar_id": calendar_id}


def setup_env_file():
    """環境変数ファイルの設定"""
    print("\n🔧 環境設定ファイルの作成")
    print("-" * 30)

    # 必要なディレクトリを作成
    ensure_directory("config")
    ensure_directory("credentials")

    # 既存設定をチェック
    env_file_path = Path("config/.env")
    existing_config = {}

    if env_file_path.exists():
        existing_config = parse_existing_env(env_file_path)
        print(f"📋 既存の設定ファイルが見つかりました: {env_file_path}")
        print("選択してください：")
        print("  y: 上書きする")
        print("  b: バックアップしてから上書きする")
        print("  N: キャンセル (デフォルト)")

        choice = input("選択 (y/b/N): ").lower()

        if choice == "b":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(f"config/.env.backup_{timestamp}")
            try:
                env_file_path.rename(backup_path)
                print(f"💾 既存設定をバックアップしました: {backup_path}")
            except Exception as e:
                print(f"❌ バックアップ作成エラー: {e}")
                return False
        elif choice != "y":
            print("❌ 設定をキャンセルしました")
            return False

    # Discord Botトークンを取得
    existing_token = existing_config.get("DISCORD_TOKEN", "")
    if existing_token:
        print(f"\n🤖 既存のDiscord Botトークン: {existing_token[:20]}...")
        use_existing = input("既存のトークンを使用しますか？ (Y/n): ").lower()
        if use_existing != "n":
            discord_token = existing_token
        else:
            discord_token = setup_discord_bot()
    else:
        discord_token = setup_discord_bot()

    if not discord_token:
        return False

    # Google Calendar設定を取得
    existing_service_file = existing_config.get("GOOGLE_SERVICE_ACCOUNT_PATH", "")
    existing_calendar_id = existing_config.get("GOOGLE_CALENDAR_ID", "")

    if existing_service_file and existing_calendar_id:
        print("\n📅 既存のGoogle Calendar設定:")
        print(f"  サービスアカウント: {existing_service_file}")
        print(f"  カレンダーID: {existing_calendar_id}")
        use_existing = input("既存の設定を使用しますか？ (Y/n): ").lower()
        if use_existing != "n":
            google_config = {
                "service_account_file": existing_service_file,
                "calendar_id": existing_calendar_id,
            }
        else:
            google_config = setup_google_calendar()
    else:
        google_config = setup_google_calendar()

    if not google_config:
        return False

    # 設定をファイルに保存
    env_content = f"""# Discord Bot設定
DISCORD_TOKEN={discord_token}

# Google Calendar設定
GOOGLE_SERVICE_ACCOUNT_PATH={google_config["service_account_file"]}
GOOGLE_CALENDAR_ID={google_config["calendar_id"]}

# ログレベル (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# タイムゾーン
TIMEZONE=Asia/Tokyo
"""

    env_file_path.write_text(env_content, encoding="utf-8")
    print(f"✅ 環境設定ファイルを作成しました: {env_file_path}")
    return True


def install_dependencies():
    """依存関係のインストール"""
    print("\n📦 依存関係のインストール")
    print("-" * 30)

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True,
        )

        print("✅ 依存関係のインストールが完了しました")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ 依存関係のインストールに失敗しました: {e}")
        print("手動で以下のコマンドを実行してください:")
        print(f"  {sys.executable} -m pip install -r requirements.txt")
        return False

    except FileNotFoundError:
        print("❌ requirements.txt が見つかりません")
        return False


def create_dockerfile():
    """Dockerfile の作成"""
    print("\n🐳 Docker設定ファイルの作成")
    print("-" * 30)

    dockerfile_content = """FROM python:3.13-slim

WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY src/ ./src/
COPY config/ ./config/
COPY credentials/ ./credentials/

# 非rootユーザーを作成
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# アプリケーションを実行
CMD ["python", "src/main.py"]
"""

    dockerfile_path = Path("docker/Dockerfile")
    ensure_directory("docker")

    if dockerfile_path.exists():
        print(f"⚠️  {dockerfile_path} は既に存在します")
        overwrite = input("上書きしますか？ (y/N): ").lower()
        if overwrite != "y":
            print("Dockerfile の作成をスキップしました")
            return True

    dockerfile_path.write_text(dockerfile_content)
    print(f"✅ {dockerfile_path} を作成しました")
    return True


def create_docker_compose():
    """docker-compose.yml の作成"""
    compose_content = """services:
  discord-bot:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: discord-calendar-bot
    restart: unless-stopped
    env_file:
      - config/.env
    volumes:
      - ./credentials:/app/credentials:ro
    environment:
      - PYTHONPATH=/app
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
"""

    compose_path = Path("docker-compose.yml")

    if compose_path.exists():
        print(f"⚠️  {compose_path} は既に存在します")
        overwrite = input("上書きしますか？ (y/N): ").lower()
        if overwrite != "y":
            print("docker-compose.yml の作成をスキップしました")
            return True

    compose_path.write_text(compose_content)
    print(f"✅ {compose_path} を作成しました")
    return True


def create_gitignore():
    """適切な .gitignore の作成"""
    print("\n📝 .gitignore の設定")
    print("-" * 30)

    gitignore_content = """# 環境設定ファイル
config/.env*
.env*

# 認証情報
credentials/
*.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Docker
.dockerignore
"""

    gitignore_path = Path(".gitignore")

    if gitignore_path.exists():
        print(f"⚠️  {gitignore_path} は既に存在します")
        overwrite = input("上書きしますか？ (y/N): ").lower()
        if overwrite != "y":
            print(".gitignore の作成をスキップしました")
            return True

    gitignore_path.write_text(gitignore_content)
    print(f"✅ {gitignore_path} を作成しました")
    return True


def main():
    """メイン関数"""
    print("🚀 Discord Calendar Bot セットアップ")
    print("=" * 40)

    # 現在のディレクトリを確認
    if not check_file_exists("main.py") and not check_file_exists("src/main.py"):
        print("❌ main.py または src/main.py が見つかりません")
        print("プロジェクトルートディレクトリで実行してください")
        return 1

    steps = [
        ("環境設定ファイルの作成", setup_env_file),
        ("依存関係のインストール", install_dependencies),
        ("Dockerfile の作成", create_dockerfile),
        ("docker-compose.yml の作成", create_docker_compose),
        (".gitignore の設定", create_gitignore),
    ]

    success_count = 0
    for step_name, step_func in steps:
        print(f"\n{step_name}を実行中...")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name}が完了しました")
            else:
                print(f"⚠️  {step_name}をスキップしました")
        except Exception as e:
            print(f"❌ {step_name}でエラーが発生しました: {e}")

    print("\n" + "=" * 40)
    print(f"セットアップ完了: {success_count}/{len(steps)} 項目")

    if success_count == len(steps):
        print("\n🎉 すべてのセットアップが完了しました！")
        print("\n次のステップ:")
        print("1. config/.env ファイルの設定を確認")
        print("2. credentials/ ディレクトリにサービスアカウントJSONを配置")
        print("3. python src/main.py でBot を起動")
        print("4. または docker-compose -f docker/docker-compose.yml up でDocker起動")
    else:
        print("\n⚠️  一部のセットアップが未完了です")
        print("エラーメッセージを確認して手動で設定してください")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ セットアップが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
