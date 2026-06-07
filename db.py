import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("DB 초기화 완료")


def is_sent(url: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_articles WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def is_first_run() -> bool:
    """sent_articles 테이블이 비어 있으면 첫 실행으로 판단."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sent_articles")
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0


def mark_sent(url: str, title: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO sent_articles (url, title, sent_at) VALUES (?, ?, ?)",
            (url, title, datetime.now()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        logger.debug(f"이미 저장된 URL: {url}")
    finally:
        conn.close()
