#!/usr/bin/env python3
"""
Discord Calendar Bot セットアップスクリプト
Google Calendar APIとDiscord Botの初期設定を行います
"""

import json
import os
import webbrowser
from pathlib import Path


def print_banner():
    """バナーを表示"""
    print("=" * 60)
    print("  Discord Calendar Bot セットアップ")
    print("=" * 60)
    print()


def setup_google_calendar():
    """Google Calendar API設定（サービスアカウント方式）"""
    print("📅 Google Calendar API設定（サービスアカウント方式）")
    print("-" * 50)

    service_account_path = "service-account-key.json"

    if not os.path.exists(service_account_path):
        print("❌ service-account-key.json が見つかりません。")
        print()
        print("以下の手順でGoogle Calendar API（サービスアカウント）を設定してください：")
        print()
        print("1. Google Cloud Console (https://console.cloud.google.com/) にアクセス")
        print("2. カレンダーを所有するアカウントAでログイン")
        print("3. 新しいプロジェクトを作成 または 既存のプロジェクトを選択")
        print("4. Google Calendar API を有効化")
        print("5. IAM と管理 → サービスアカウント → サービスアカウントを作成")
        print("6. サービスアカウント名を入力（例: discord-calendar-bot）")
        print("7. キーを作成 → JSON形式でダウンロード")
        print("8. ダウンロードしたファイルを service-account-key.json にリネーム")
        print("9. このディレクトリに配置")
        print()
        print("⚠️ 重要: サービスアカウントにカレンダーへのアクセス権を付与してください：")
        print("   - Google Calendar でカレンダー設定を開く")
        print("   - 「特定のユーザーとの共有」でサービスアカウントのメールアドレスを追加")
        print("   - 権限: 「予定の変更および共有の管理権限」を選択")
        print()

        if input("Google Cloud Consoleを開きますか？ (y/N): ").lower() == "y":
            webbrowser.open("https://console.cloud.google.com/")

        return False
    else:
        print("✅ service-account-key.json が見つかりました")

        # サービスアカウント情報を表示
        try:
            with open(service_account_path, "r") as f:
                import json

                sa_info = json.load(f)
                print(f"📧 サービスアカウントメール: {sa_info.get('client_email', 'N/A')}")
                print()
                print("📋 カレンダー共有の確認:")
                print("1. Google Calendar (https://calendar.google.com/) を開く")
                print("2. 対象のカレンダーの設定を開く")
                print("3. 「特定のユーザーとの共有」に以下のメールアドレスが追加されているか確認:")
                print(f"   {sa_info.get('client_email', 'N/A')}")
                print("4. 権限が「予定の変更および共有の管理権限」になっているか確認")

        except Exception as e:
            print(f"⚠️ サービスアカウント情報の読み取りに失敗: {e}")

        return True


def setup_discord_bot():
    """Discord Bot設定"""
    print("\n🤖 Discord Bot設定")
    print("-" * 30)

    print("以下の手順でDiscord Botを設定してください：")
    print()
    print("1. Discord Developer Portal (https://discord.com/developers/applications) にアクセス")
    print("2. 'New Application' をクリックして新しいアプリケーションを作成")
    print("3. 左側メニューの 'Bot' をクリック")
    print("4. 'Add Bot' をクリック")
    print("5. 'Token' セクションで 'Copy' をクリックしてトークンをコピー")
    print("6. Bot Permissions:")
    print("   - Send Messages")
    print("   - Use Slash Commands")
    print("   - Embed Links")
    print("   - Read Message History")
    print()

    if input("Discord Developer Portalを開きますか？ (y/N): ").lower() == "y":
        webbrowser.open("https://discord.com/developers/applications")

    print()
    token = input("Discord Bot Tokenを入力してください: ").strip()

    if not token:
        print("❌ Tokenが入力されませんでした")
        return None

    return token


def setup_env_file():
    """環境変数ファイルの設定"""
    print("\n🔧 環境設定ファイルの作成")
    print("-" * 30)

    # Discord Botトークンを取得
    discord_token = setup_discord_bot()
    if not discord_token:
        return False

    print()
    print("リマインダーを送信するDiscordチャンネルを設定してください。")
    print("チャンネルIDの取得方法：")
    print("1. Discordで開発者モードを有効化 (設定 → 詳細設定 → 開発者モード)")
    print("2. 対象のチャンネルを右クリック → 'IDをコピー'")
    print()

    channel_id = input("リマインダーチャンネルID (オプション): ").strip()

    print()
    print("カレンダーID設定:")
    print("- 'primary' を使用する場合: メインカレンダーを操作")
    print("- 特定のカレンダーを使用する場合:")
    print("  1. Google Calendar で対象カレンダーの設定を開く")
    print("  2. カレンダーIDをコピー（例: abc123@group.calendar.google.com）")
    print()

    calendar_id = input("使用するカレンダーID (デフォルト: primary): ").strip()
    if not calendar_id:
        calendar_id = "primary"

    print()
    print("委任ユーザー設定（Google Workspace環境の場合）:")
    print("- 個人アカウントの場合: 空のままでOK")
    print("- 組織アカウントで特定ユーザーとして動作する場合: メールアドレスを入力")
    print()

    delegated_user = input("委任ユーザーのメールアドレス (オプション): ").strip()

    # .envファイルを作成
    env_content = f"""# Discord Bot設定
DISCORD_TOKEN={discord_token}

# Google Calendar API設定（サービスアカウント方式）
GOOGLE_SERVICE_ACCOUNT_PATH=service-account-key.json
GOOGLE_CALENDAR_ID={calendar_id}"""

    if delegated_user:
        env_content += f"\nGOOGLE_DELEGATED_USER={delegated_user}"
    else:
        env_content += "\n# GOOGLE_DELEGATED_USER=user@yourdomain.com"

    env_content += """

# その他設定
TIMEZONE=Asia/Tokyo"""

    if channel_id:
        env_content += f"\nREMINDER_CHANNEL_ID={channel_id}"
    else:
        env_content += "\n# REMINDER_CHANNEL_ID=your_reminder_channel_id_here"

    with open(".env", "w") as f:
        f.write(env_content)

    print("✅ .env ファイルが作成されました")
    return True


def install_dependencies():
    """依存関係のインストール"""
    print("\n📦 依存関係のインストール")
    print("-" * 30)

    try:
        import subprocess

        result = subprocess.run(["uv", "sync"], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ 依存関係のインストールが完了しました")
            return True
        else:
            print(f"❌ インストールエラー: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ 'uv' コマンドが見つかりません")
        print(
            "pip install discord.py google-api-python-client google-auth google-auth-oauthlib python-dateutil pytz python-dotenv を実行してください"
        )
        return False


def main():
    """メイン関数"""
    print_banner()

    # Google Calendar API設定
    if not setup_google_calendar():
        print("\n❌ Google Calendar APIの設定が完了していません")
        print("設定完了後、再度このスクリプトを実行してください")
        return

    # 環境変数ファイル設定
    if not setup_env_file():
        print("\n❌ 環境設定の作成に失敗しました")
        return

    # 依存関係インストール
    if not install_dependencies():
        print("\n⚠️  依存関係のインストールを手動で行ってください")

    print("\n" + "=" * 60)
    print("  🎉 セットアップ完了！")
    print("=" * 60)
    print()
    print("次の手順：")
    print("1. python main.py を実行してBotを起動")
    print("2. DiscordでBotを招待 (招待URLはDeveloper Portalで生成)")
    print("3. !help_calendar でコマンド一覧を確認")
    print()
    print("コマンド例：")
    print("  !add_event 2024-08-15 10:00-11:00 会議")
    print("  !list_events 7")
    print("  !delete_event 会議")
    print()


if __name__ == "__main__":
    main()
