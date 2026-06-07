import feedparser
import logging
from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED

logger = logging.getLogger(__name__)

_RSS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
}


def collect_rss() -> list[dict]:
    articles = []
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], request_headers=_RSS_HEADERS)
            if not feed.entries:
                reason = str(feed.bozo_exception) if feed.bozo else "항목 없음"
                logger.warning(f"RSS 수집 실패 [{feed_info['name']}]: {reason}")
                continue

            count = 0
            for entry in feed.entries:
                if count >= MAX_ARTICLES_PER_FEED:
                    break
                url = entry.get("link", "")
                if not url:
                    continue
                articles.append({
                    "title": entry.get("title", "제목 없음").strip(),
                    "url": url.strip(),
                    "summary": _extract_summary(entry),
                    "published": entry.get("published", ""),
                    "source": feed_info["name"],
                })
                count += 1

            logger.info(f"{feed_info['name']}: {count}개 수집")
        except Exception as e:
            logger.error(f"RSS 오류 [{feed_info['name']}]: {e}")

    return articles


def _extract_summary(entry) -> str:
    for field in ("summary", "description", "content"):
        val = entry.get(field, "")
        if isinstance(val, list) and val:
            val = val[0].get("value", "")
        if val:
            # feedparser occasionally returns HTML; strip tags crudely
            import re
            val = re.sub(r"<[^>]+>", " ", str(val))
            val = " ".join(val.split())
            return val[:800]
    return ""
