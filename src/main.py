import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import discord
import pytz
from discord.ext import commands, tasks
from dotenv import load_dotenv

from google_calendar import GoogleCalendarManager
from reminder_service import ReminderService

# 環境変数の読み込み
load_dotenv("config/.env")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord Bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Google Calendar Manager
gcal_manager = GoogleCalendarManager()

# Reminder Service
reminder_service = ReminderService(bot, gcal_manager)


def get_calendar_link() -> Optional[str]:
    """カレンダーのWebリンクを取得"""
    return os.getenv("GOOGLE_CALENDAR_WEB_URL")


def add_calendar_link_to_embed(embed: discord.Embed) -> discord.Embed:
    """Embedにカレンダーリンクを追加"""
    calendar_url = get_calendar_link()
    if calendar_url:
        embed.add_field(
            name="🔗 カレンダーを開く",
            value=f"[Google Calendar で確認]({calendar_url})",
            inline=False,
        )
    return embed


@bot.event
async def on_ready():
    """Bot起動時の処理"""
    logger.info("=" * 50)
    logger.info("🤖 Discord Calendar Bot 起動開始")
    logger.info("=" * 50)
    logger.info(f"👤 Bot ユーザー: {bot.user} (ID: {bot.user.id})")
    logger.info(f"🌐 接続サーバー数: {len(bot.guilds)}")

    # Google Calendar初期化
    logger.info("📅 Google Calendar 初期化開始...")
    try:
        await gcal_manager.initialize()
        logger.info("✅ Google Calendar 初期化完了")
    except Exception as e:
        logger.error(f"❌ Google Calendar 初期化失敗: {e}")
        return

    # リマインダーサービス開始
    logger.info("🔔 リマインダーサービス開始...")
    reminder_service.start_reminder_loop()

    logger.info("=" * 50)
    logger.info("✅ Discord Calendar Bot 起動完了！")
    logger.info("💡 !help_calendar でコマンド一覧を確認できます")
    logger.info("=" * 50)


@bot.command(name="add_event")
async def add_event(ctx, *, event_description: str):
    """
    カレンダーにイベントを追加
    使用例: !add_event 2025-08-14 10:00-11:00 会議
    """
    try:
        logger.info(f"📝 イベント追加要求: {event_description} (by {ctx.author})")
        event = await gcal_manager.parse_and_create_event(event_description)
        if event:
            logger.info(f"✅ イベント追加成功: {event['summary']}")
            embed = discord.Embed(
                title="✅ イベントが追加されました",
                description=f"**{event['summary']}**\n"
                f"📅 {event['start']['dateTime'][:10]}\n"
                f"🕐 {event['start']['dateTime'][11:16]} - {event['end']['dateTime'][11:16]}",
                color=0x00FF00,
            )
            embed = add_calendar_link_to_embed(embed)
            await ctx.send(embed=embed)
        else:
            logger.warning(f"⚠️ イベント追加失敗: 形式エラー - {event_description}")
            await ctx.send("❌ イベントの追加に失敗しました。形式を確認してください。")
    except Exception as e:
        logger.error(f"❌ イベント追加エラー: {e}")
        await ctx.send(f"❌ エラーが発生しました: {str(e)}")


@bot.command(name="list_events")
async def list_events(ctx, days: int = 7):
    """
    今後のイベントを表示
    使用例: !list_events 7
    """
    try:
        events = await gcal_manager.get_upcoming_events(days)
        if not events:
            await ctx.send("📅 今後のイベントはありません。")
            return

        embed = discord.Embed(title=f"📅 今後 {days} 日のイベント", color=0x0099FF)

        for event in events[:10]:  # 最大10件まで表示
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            if "T" in start_time:
                # 日時形式
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                time_str = dt.strftime("%m/%d %H:%M")
            else:
                # 日付のみ
                dt = datetime.fromisoformat(start_time)
                time_str = dt.strftime("%m/%d (終日)")

            embed.add_field(name=event["summary"], value=f"🕐 {time_str}", inline=False)

        embed = add_calendar_link_to_embed(embed)
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"イベント取得エラー: {e}")
        await ctx.send(f"❌ エラーが発生しました: {str(e)}")


@bot.command(name="delete_event")
async def delete_event(ctx, *, event_title: str):
    """
    イベントを削除
    使用例: !delete_event 会議
    """
    try:
        success = await gcal_manager.delete_event_by_title(event_title)
        if success:
            embed = discord.Embed(
                title="✅ イベントが削除されました",
                description=f"「{event_title}」を削除しました",
                color=0xFF9900,
            )
            embed = add_calendar_link_to_embed(embed)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ 「{event_title}」というイベントが見つかりませんでした。")
    except Exception as e:
        logger.error(f"イベント削除エラー: {e}")
        await ctx.send(f"❌ エラーが発生しました: {str(e)}")


@bot.command(name="help_calendar")
async def help_calendar(ctx):
    """カレンダーボットのヘルプを表示"""
    # 今日の日付を取得（例で使用）
    today = datetime.now().strftime("%Y-%m-%d")

    embed = discord.Embed(
        title="📅 カレンダーボット ヘルプ",
        description="Google カレンダーと連携するDiscord botです",
        color=0x0099FF,
    )

    embed.add_field(
        name="!add_event <詳細>",
        value=f"イベントを追加\n例: `!add_event {today} 10:00-11:00 会議`",
        inline=False,
    )

    embed.add_field(
        name="!list_events [日数]", value="今後のイベントを表示\n例: `!list_events 7`", inline=False
    )

    embed.add_field(
        name="!delete_event <タイトル>",
        value="イベントを削除\n例: `!delete_event 会議`",
        inline=False,
    )

    embed = add_calendar_link_to_embed(embed)
    await ctx.send(embed=embed)


def main():
    """メイン関数"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKENが設定されていません")
        return

    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Bot実行エラー: {e}")


if __name__ == "__main__":
    main()
