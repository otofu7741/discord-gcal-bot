import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleCalendarManager:
    """Google Calendar API管理クラス（サービスアカウント方式）"""

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self):
        self.service = None
        self.timezone = pytz.timezone(os.getenv("TIMEZONE", "Asia/Tokyo"))
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")  # カレンダーID

    async def initialize(self):
        """Google Calendar APIの初期化（サービスアカウント方式）"""
        try:
            service_account_path = os.getenv(
                "GOOGLE_SERVICE_ACCOUNT_PATH", "service-account-key.json"
            )

            if not os.path.exists(service_account_path):
                raise FileNotFoundError(
                    f"サービスアカウントキーファイル {service_account_path} が見つかりません。\n"
                    "Google Cloud Consoleからサービスアカウントキー（JSON）をダウンロードしてください。"
                )

            # サービスアカウント認証情報を読み込み
            print(f"🔑 サービスアカウントキー読み込み: {service_account_path}")
            creds = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=self.SCOPES
            )

            # サービスアカウント情報を表示
            service_account_email = creds.service_account_email
            project_id = getattr(creds, "_project_id", "N/A")
            print(f"📧 サービスアカウント: {service_account_email}")
            print(f"🏗️ プロジェクトID: {project_id}")

            # 委任が必要な場合（特定ユーザーとして動作する場合）
            delegated_user = os.getenv("GOOGLE_DELEGATED_USER")
            if delegated_user:
                creds = creds.with_subject(delegated_user)
                print(f"� 委任ユーザー: {delegated_user}")

            self.service = build("calendar", "v3", credentials=creds)
            print("✅ Google Calendar API接続成功（サービスアカウント方式）")

            # 接続テスト: カレンダー情報を取得
            await self._test_calendar_connection()

        except Exception as e:
            print(f"❌ Google Calendar API初期化エラー: {e}")
            raise

    async def _test_calendar_connection(self):
        """カレンダー接続テスト"""
        try:
            print("🔍 カレンダー接続テスト開始...")

            # カレンダー情報を取得
            calendar_info = self.service.calendars().get(calendarId=self.calendar_id).execute()

            print(f"📅 カレンダー名: {calendar_info.get('summary', 'N/A')}")
            print(f"📧 カレンダーID: {self.calendar_id}")
            print(f"🌍 タイムゾーン: {calendar_info.get('timeZone', 'N/A')}")

            # 今後1日のイベント数を確認
            now = datetime.utcnow()
            time_min = now.isoformat() + "Z"
            time_max = (now + timedelta(days=1)).isoformat() + "Z"

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            print(f"📊 今後24時間のイベント数: {len(events)}件")

            if events:
                print("📝 直近のイベント:")
                for i, event in enumerate(events[:3], 1):
                    title = event.get("summary", "タイトルなし")
                    start_time = event["start"].get("dateTime", event["start"].get("date", "N/A"))
                    print(f"   {i}. {title} ({start_time[:16]})")

            print("✅ カレンダー接続テスト完了")

        except HttpError as e:
            if e.resp.status == 404:
                print(f"❌ カレンダーが見つかりません（ID: {self.calendar_id}）")
                print("💡 確認事項:")
                print("   - カレンダーIDが正しいか")
                print("   - サービスアカウントにカレンダーが共有されているか")
            elif e.resp.status == 403:
                print("❌ カレンダーへのアクセス権限がありません")
                print("💡 確認事項:")
                print("   - サービスアカウントにカレンダーが共有されているか")
                print("   - 共有権限が「予定の変更および共有の管理権限」になっているか")
            else:
                print(f"❌ カレンダー接続エラー: {e}")
            raise
        except Exception as e:
            print(f"❌ カレンダー接続テストエラー: {e}")
            raise

    async def parse_and_create_event(self, event_description: str) -> Optional[Dict]:
        """
        テキストからイベントを解析して作成
        例: "2024-08-15 10:00-11:00 会議"
        """
        try:
            # 基本的なパターンマッチング
            # YYYY-MM-DD HH:MM-HH:MM タイトル の形式
            pattern = r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.+)"
            match = re.match(pattern, event_description.strip())

            if not match:
                # より柔軟なパターンを試す
                # MM/DD HH:MM-HH:MM タイトル の形式
                pattern2 = r"(\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.+)"
                match = re.match(pattern2, event_description.strip())

                if match:
                    date_str, start_time, end_time, title = match.groups()
                    # 現在の年を追加
                    current_year = datetime.now().year
                    date_str = f"{current_year}-{date_str.replace('/', '-').zfill(5)}"
                else:
                    return None
            else:
                date_str, start_time, end_time, title = match.groups()

            # 日時を構築
            start_datetime = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")

            # タイムゾーンを設定
            start_datetime = self.timezone.localize(start_datetime)
            end_datetime = self.timezone.localize(end_datetime)

            # イベントデータを作成
            event = {
                "summary": title.strip(),
                "start": {
                    "dateTime": start_datetime.isoformat(),
                    "timeZone": str(self.timezone),
                },
                "end": {
                    "dateTime": end_datetime.isoformat(),
                    "timeZone": str(self.timezone),
                },
            }

            # Google Calendarにイベントを作成
            print("🔄 カレンダーへイベント挿入中...")
            print(f"📋 カレンダーID: {self.calendar_id}")
            print(f"📝 イベントデータ: {event}")

            created_event = (
                self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            )

            print(f"✅ イベント作成成功: {created_event.get('id', 'N/A')}")
            print(f"🔗 イベントリンク: {created_event.get('htmlLink', 'N/A')}")

            return created_event

        except HttpError as e:
            print(f"❌ Google Calendar API エラー: {e}")
            print(f"   ステータス: {e.resp.status}")
            print(f"   詳細: {e.content}")
            return None
        except Exception as e:
            print(f"❌ イベント作成エラー: {e}")
            print(f"   エラータイプ: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            return None

    async def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """今後のイベントを取得"""
        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + "Z"
            time_max = (now + timedelta(days=days)).isoformat() + "Z"

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            return events

        except HttpError as e:
            print(f"イベント取得エラー: {e}")
            return []

    async def delete_event_by_title(self, title: str) -> bool:
        """タイトルでイベントを検索して削除"""
        try:
            # 今後30日のイベントを検索
            events = await self.get_upcoming_events(30)

            for event in events:
                if event.get("summary", "").lower() == title.lower():
                    self.service.events().delete(
                        calendarId=self.calendar_id, eventId=event["id"]
                    ).execute()
                    print(f"イベント削除: {event['summary']}")
                    return True

            return False

        except HttpError as e:
            print(f"イベント削除エラー: {e}")
            return False

    async def get_events_for_reminder(self, minutes_ahead: int = 10) -> List[Dict]:
        """リマインダー用のイベントを取得"""
        try:
            now = datetime.utcnow()
            time_min = (now + timedelta(minutes=minutes_ahead - 1)).isoformat() + "Z"
            time_max = (now + timedelta(minutes=minutes_ahead + 1)).isoformat() + "Z"

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return events_result.get("items", [])

        except HttpError as e:
            print(f"リマインダー用イベント取得エラー: {e}")
            return []
