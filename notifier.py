import asyncio
import sys
import logging
from telegram import Bot
from telegram.error import TelegramError
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

# Windows requires SelectorEventLoop for telegram's httpx client
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

CATEGORY_EMOJI = {
    "행정명령": "🏛️",
    "투자뉴스": "💰",
    "금융뉴스": "🏦",
    "경제뉴스": "📈",
    "기술뉴스": "💻",
}
MAX_MESSAGE_LENGTH = 4000


def format_message(article: dict) -> str:
    emoji = CATEGORY_EMOJI.get(article["category"], "📰")
    category = article["category"]
    published = article.get("published", "") or "날짜 미상"

    lines = [
        f"{emoji} [{category}]",
        "",
        f"제목: {article['korean_title']}",
        "",
        "📋 요약",
        article["summary"],
        "",
        "🇰🇷 한국 영향",
        article["korea_impact"],
        "",
        f"🔗 {article['url']}",
        f"📅 {published}",
    ]
    message = "\n".join(lines)

    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH] + "…"

    return message


async def _send_async(text: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    async with bot:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            disable_web_page_preview=True,
        )


def send_message(text: str):
    try:
        asyncio.run(_send_async(text))
        logger.info("텔레그램 전송 완료")
    except TelegramError as e:
        logger.error(f"텔레그램 오류: {e}")
    except Exception as e:
        logger.error(f"전송 실패: {e}")


def notify_article(article: dict):
    message = format_message(article)
    send_message(message)
