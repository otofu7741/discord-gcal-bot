# Discord Calendar Bot

Google カレンダーと連携するDiscord botです。**サービスアカウント方式**を使用してカレンダーの予定の追加・編集・削除と、Discordへのリマインド機能を提供します。

## 機能

- 📅 **カレンダー操作**
  - イベントの追加
  - イベントの一覧表示
  - イベントの削除

- 🔔 **リマインダー機能**
  - イベント開始10分前の自動通知
  - 指定チャンネルへの通知送信

- 🤖 **Discord連携**
  - スラッシュコマンド対応
  - リッチエンベッド表示
  - エラーハンドリング
  - **全ての返答にカレンダーリンクを埋め込み**

- 🔐 **サービスアカウント方式**
  - OAuth認証不要
  - サーバー環境での安定した動作
  - 特定ユーザーのカレンダーへの安全なアクセス

- 🔗 **カレンダーリンク機能**
  - Discord の全ての返答にGoogle Calendarへのリンクを表示
  - ワンクリックでWebカレンダーにアクセス可能

## セットアップ

### 1. プロジェクトのクローン

```bash
git clone <repository-url>
cd discord-gcal-bot
```

### 2. 自動セットアップ

```bash
python setup.py
```

このスクリプトが以下を行います：
- Google Calendar API設定の確認
- Discord Bot設定
- 環境変数ファイルの作成
- 依存関係のインストール

### 3. 手動セットアップ（必要に応じて）

#### Google Calendar API設定（サービスアカウント方式）

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. **カレンダーを所有するアカウントA**でログイン
3. 新しいプロジェクトを作成または既存のプロジェクトを選択
4. Google Calendar API を有効化
5. **サービスアカウントを作成**:
   - IAM と管理 → サービスアカウント → サービスアカウントを作成
   - サービスアカウント名を入力（例: discord-calendar-bot）
   - キーを作成 → JSON形式でダウンロード
   - ダウンロードしたファイルを `service-account-key.json` にリネーム
   - プロジェクトルートに配置

6. **カレンダーの共有設定**（重要）:
   - Google Calendar で対象のカレンダー設定を開く
   - 「特定のユーザーとの共有」でサービスアカウントのメールアドレスを追加
   - 権限: **「予定の変更および共有の管理権限」**を選択

#### Discord Bot作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 新しいアプリケーションを作成
3. Bot タブでBotを作成
4. 必要な権限を設定：
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History

#### 環境変数設定

`.env` ファイルを作成：

```env
DISCORD_TOKEN=your_discord_bot_token
GOOGLE_SERVICE_ACCOUNT_PATH=service-account-key.json
GOOGLE_CALENDAR_ID=primary
# GOOGLE_DELEGATED_USER=user@yourdomain.com  # Google Workspace環境の場合
TIMEZONE=Asia/Tokyo
REMINDER_CHANNEL_ID=your_reminder_channel_id
```

### 4. 依存関係のインストール

```bash
# uvを使用する場合
uv sync

# pipを使用する場合
pip install discord.py google-api-python-client google-auth python-dateutil pytz python-dotenv
```

## 使用方法

### Bot起動

```bash
python main.py
```

サービスアカウント方式のため、ブラウザでの認証は不要です。

### Discord コマンド

#### イベント追加
```
!add_event 2024-08-15 10:00-11:00 会議
!add_event 8/15 14:00-15:30 プレゼン準備
```

#### イベント一覧表示
```
!list_events          # 今後7日のイベント
!list_events 14       # 今後14日のイベント
```

#### イベント削除
```
!delete_event 会議
```

#### ヘルプ表示
```
!help_calendar
```

### リマインダー機能

- イベント開始の10分前に自動通知
- 指定したチャンネルにリッチエンベッドで送信
- 通知の重複を防ぐ仕組み内蔵

## ファイル構成

```
discord-gcal-bot/
├── main.py                      # メインのBot実行ファイル
├── google_calendar.py           # Google Calendar API管理（サービスアカウント方式）
├── reminder_service.py          # リマインダー機能
├── setup.py                    # セットアップスクリプト
├── pyproject.toml              # プロジェクト設定
├── .env.example                # 環境変数テンプレート
├── .env                        # 環境変数（作成される）
├── service-account-key.json    # サービスアカウントキー（Google Cloudから取得）
└── README.md                   # このファイル
```

## トラブルシューティング

### Google Calendar API エラー

- `service-account-key.json` が正しく配置されているか確認
- Google Cloud Console でCalendar API が有効化されているか確認
- サービスアカウントがカレンダーに共有されているか確認
- 共有権限が「予定の変更および共有の管理権限」になっているか確認

### サービスアカウントのメールアドレス確認

サービスアカウントのメールアドレスは以下で確認できます：
```bash
python -c "import json; print(json.load(open('service-account-key.json'))['client_email'])"
```

### Discord Bot エラー

- Bot トークンが正しく設定されているか確認
- Bot がサーバーに招待されているか確認
- 必要な権限が付与されているか確認

### リマインダーが動作しない

- `REMINDER_CHANNEL_ID` が正しく設定されているか確認
- Bot がそのチャンネルにメッセージを送信する権限があるか確認

## ライセンス

MIT License

## 貢献

プルリクエストや Issue の報告を歓迎します。

## サポート

問題が発生した場合は、以下を確認してください：

1. 依存関係が正しくインストールされているか
2. 環境変数が正しく設定されているか  
3. Google Calendar API とDiscord Bot の設定が正しいか

それでも解決しない場合は、Issue を作成してください。
