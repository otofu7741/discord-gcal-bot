import asyncio
import os
from datetime import datetime, timedelta
from typing import Set

import discord
import pytz

class ReminderService:
    """リマインダーサービスクラス"""
    
    def __init__(self, bot, gcal_manager):
        self.bot = bot
        self.gcal_manager = gcal_manager
        self.timezone = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Tokyo'))
        self.reminder_channel_id = int(os.getenv('REMINDER_CHANNEL_ID', 0))
        self.notified_events: Set[str] = set()  # 通知済みイベントのID
        self.is_running = False
        
    def start_reminder_loop(self):
        """リマインダーループを開始"""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self._reminder_loop())
            print("✅ リマインダーサービス開始")
    
    async def _reminder_loop(self):
        """リマインダーのメインループ"""
        while self.is_running:
            try:
                await self._check_and_send_reminders()
                await asyncio.sleep(60)  # 1分ごとにチェック
            except Exception as e:
                print(f"リマインダーループエラー: {e}")
                await asyncio.sleep(60)
    
    async def _check_and_send_reminders(self):
        """リマインダーをチェックして送信"""
        try:
            # 10分後のイベントを取得
            events = await self.gcal_manager.get_events_for_reminder(10)
            
            for event in events:
                event_id = event.get('id')
                if event_id in self.notified_events:
                    continue  # 既に通知済み
                
                await self._send_reminder(event)
                self.notified_events.add(event_id)
                
            # 過去のイベントIDをクリーンアップ（1時間前より古いものを削除）
            await self._cleanup_notified_events()
            
        except Exception as e:
            print(f"リマインダーチェックエラー: {e}")
    
    async def _send_reminder(self, event):
        """個別のリマインダーを送信"""
        try:
            if not self.reminder_channel_id:
                print("リマインダーチャンネルIDが設定されていません")
                return
            
            channel = self.bot.get_channel(self.reminder_channel_id)
            if not channel:
                print(f"チャンネル {self.reminder_channel_id} が見つかりません")
                return
            
            # イベント情報を取得
            title = event.get('summary', 'タイトルなし')
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            
            # 時刻を日本時間に変換
            if 'T' in start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                dt_jst = dt.astimezone(self.timezone)
                time_str = dt_jst.strftime('%H:%M')
                date_str = dt_jst.strftime('%m/%d')
            else:
                dt = datetime.fromisoformat(start_time)
                time_str = "終日"
                date_str = dt.strftime('%m/%d')
            
            # リマインダーメッセージを作成
            embed = discord.Embed(
                title="🔔 イベントリマインダー",
                description=f"**{title}**\n📅 {date_str} {time_str}",
                color=0xff6b6b
            )
            
            embed.add_field(
                name="⏰ 開始まで",
                value="約10分",
                inline=True
            )
            
            # イベントの場所があれば追加
            if 'location' in event:
                embed.add_field(
                    name="📍 場所",
                    value=event['location'],
                    inline=True
                )
            
            # イベントの説明があれば追加
            if 'description' in event:
                description = event['description']
                if len(description) > 100:
                    description = description[:100] + "..."
                embed.add_field(
                    name="📝 詳細",
                    value=description,
                    inline=False
                )
            
            embed.set_footer(text="Google Calendar連携")
            
            await channel.send(embed=embed)
            print(f"リマインダー送信: {title}")
            
        except Exception as e:
            print(f"リマインダー送信エラー: {e}")
    
    async def _cleanup_notified_events(self):
        """通知済みイベントIDのクリーンアップ"""
        try:
            # 現在時刻から1時間前より古いイベントのIDを削除
            # 実際の実装では、イベントIDから時刻を判定するか、
            # 別途タイムスタンプを保存する必要があります
            # ここでは簡単のため、定期的に全てクリアします
            if len(self.notified_events) > 100:  # 100件を超えたらクリア
                self.notified_events.clear()
                
        except Exception as e:
            print(f"通知済みイベントクリーンアップエラー: {e}")
    
    def stop_reminder_loop(self):
        """リマインダーループを停止"""
        self.is_running = False
        print("リマインダーサービス停止")
    
    async def send_daily_schedule(self):
        """毎日のスケジュールを送信"""
        try:
            if not self.reminder_channel_id:
                return
            
            channel = self.bot.get_channel(self.reminder_channel_id)
            if not channel:
                return
            
            # 今日のイベントを取得
            events = await self.gcal_manager.get_upcoming_events(1)
            
            today = datetime.now(self.timezone).strftime('%m/%d (%a)')
            
            if not events:
                embed = discord.Embed(
                    title=f"📅 今日 {today} の予定",
                    description="今日の予定はありません。",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title=f"📅 今日 {today} の予定",
                    color=0x0099ff
                )
                
                for event in events:
                    title = event.get('summary', 'タイトルなし')
                    start_time = event['start'].get('dateTime', event['start'].get('date'))
                    
                    if 'T' in start_time:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        dt_jst = dt.astimezone(self.timezone)
                        time_str = dt_jst.strftime('%H:%M')
                    else:
                        time_str = "終日"
                    
                    embed.add_field(
                        name=title,
                        value=f"🕐 {time_str}",
                        inline=False
                    )
            
            embed.set_footer(text="良い一日をお過ごしください！")
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"日次スケジュール送信エラー: {e}")
