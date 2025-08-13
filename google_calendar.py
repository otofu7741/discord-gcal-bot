import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from dateutil import parser

class GoogleCalendarManager:
    """Google Calendar API管理クラス（サービスアカウント方式）"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.service = None
        self.timezone = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Tokyo'))
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')  # カレンダーID
        
    async def initialize(self):
        """Google Calendar APIの初期化（サービスアカウント方式）"""
        try:
            service_account_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH', 'service-account-key.json')
            
            if not os.path.exists(service_account_path):
                raise FileNotFoundError(
                    f"サービスアカウントキーファイル {service_account_path} が見つかりません。\n"
                    "Google Cloud Consoleからサービスアカウントキー（JSON）をダウンロードしてください。"
                )
            
            # サービスアカウント認証情報を読み込み
            creds = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=self.SCOPES
            )
            
            # 委任が必要な場合（特定ユーザーとして動作する場合）
            delegated_user = os.getenv('GOOGLE_DELEGATED_USER')
            if delegated_user:
                creds = creds.with_subject(delegated_user)
                print(f"🔑 委任ユーザー: {delegated_user}")
            
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar API接続成功（サービスアカウント方式）")
            
        except Exception as e:
            print(f"❌ Google Calendar API初期化エラー: {e}")
            raise
    
    async def parse_and_create_event(self, event_description: str) -> Optional[Dict]:
        """
        テキストからイベントを解析して作成
        例: "2024-08-15 10:00-11:00 会議"
        """
        try:
            # 基本的なパターンマッチング
            # YYYY-MM-DD HH:MM-HH:MM タイトル の形式
            pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.+)'
            match = re.match(pattern, event_description.strip())
            
            if not match:
                # より柔軟なパターンを試す
                # MM/DD HH:MM-HH:MM タイトル の形式
                pattern2 = r'(\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.+)'
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
                'summary': title.strip(),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': str(self.timezone),
                },
            }
            
            # Google Calendarにイベントを作成
            created_event = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            return created_event
            
        except Exception as e:
            print(f"イベント作成エラー: {e}")
            return None
    
    async def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """今後のイベントを取得"""
        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
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
                if event.get('summary', '').lower() == title.lower():
                    self.service.events().delete(
                        calendarId=self.calendar_id,
                        eventId=event['id']
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
            time_min = (now + timedelta(minutes=minutes_ahead - 1)).isoformat() + 'Z'
            time_max = (now + timedelta(minutes=minutes_ahead + 1)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as e:
            print(f"リマインダー用イベント取得エラー: {e}")
            return []
