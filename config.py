import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_FEEDS = [
    {"name": "Federal Register",  "url": "https://www.federalregister.gov/articles/search.rss?conditions[type][]=PRESDOCU"},
    {"name": "Federal Reserve",   "url": "https://www.federalreserve.gov/feeds/press_all.xml"},
    {"name": "SEC",               "url": "https://www.sec.gov/news/pressreleases.rss"},
    {"name": "White House",       "url": "https://www.whitehouse.gov/news/feed/"},
    {"name": "Congress",          "url": "https://www.congress.gov/rss/most-viewed-bills.xml"},
    {"name": "Reuters Business",  "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "AP News",           "url": "https://feeds.apnews.com/rss/topnews"},
]

SCRAPER_TARGETS = [
    # Treasury·FTC는 RSS 없음 → 스크래핑으로 수집
    {"name": "USTR",     "url": "https://ustr.gov/about-us/policy-offices/press-office/press-releases"},
    {"name": "NIST",     "url": "https://www.nist.gov/news-events/news"},
    {"name": "Treasury", "url": "https://home.treasury.gov/news/press-releases"},
    {"name": "FTC",      "url": "https://www.ftc.gov/news-events/news/press-releases"},
]

KEYWORDS = {
    "행정명령": ["executive order", "presidential action", "proclamation", "memorandum"],
    "투자뉴스": ["investment", "billion", "factory", "plant", "fdi", "announces investment", "pledges", "job creation", "manufacturing"],
    "금융뉴스": ["federal reserve", "interest rate", "sec", "fdic", "banking", "monetary", "basel", "bond"],
    "경제뉴스": ["tariff", "trade", "gdp", "inflation", "ustr", "export", "import", "sanctions", "supply chain"],
    "기술뉴스": ["ai", "semiconductor", "chips", "cyber", "data privacy", "nist", "export control"],
}

MODEL = "claude-haiku-4-5-20251001"
DB_PATH = "us_policy_bot.db"
MAX_ARTICLES_PER_FEED = 5
REQUEST_TIMEOUT = 15
