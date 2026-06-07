import requests
from bs4 import BeautifulSoup
import logging
from config import MAX_ARTICLES_PER_FEED, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _get_soup(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.error(f"GET 실패 [{url}]: {e}")
        return None


def _make_absolute(href: str, base: str) -> str:
    if href.startswith("http"):
        return href
    from urllib.parse import urljoin
    return urljoin(base, href)


def scrape_ustr() -> list[dict]:
    url = "https://ustr.gov/about-us/policy-offices/press-office/press-releases"
    soup = _get_soup(url)
    if not soup:
        return []

    articles = []
    # USTR is Drupal-based; try multiple selectors for resilience
    selectors = [
        "div.view-content article a",
        "div.views-row h3 a",
        "div.views-row a",
        "ul.press-releases li a",
    ]
    links = []
    for sel in selectors:
        links = soup.select(sel)
        if links:
            break

    seen = set()
    for a in links:
        if len(articles) >= MAX_ARTICLES_PER_FEED:
            break
        title = a.get_text(strip=True)
        href = _make_absolute(a.get("href", ""), url)
        # 주(州) 페이지 등 비(非) 보도자료 URL 제외
        if not href or href in seen or not title:
            continue
        if "press-release" not in href.lower():
            continue
        seen.add(href)
        articles.append({"title": title, "url": href, "summary": "", "published": "", "source": "USTR"})

    logger.info(f"USTR: {len(articles)}개 수집")
    return articles


def scrape_nist() -> list[dict]:
    url = "https://www.nist.gov/news-events/news"
    soup = _get_soup(url)
    if not soup:
        return []

    articles = []
    selectors = [
        "article h2 a",
        "div.views-row h3 a",
        "div.news-listing a",
        "h2.nist-page__title a",
        "a.nist-teaser__title",
    ]
    links = []
    for sel in selectors:
        links = soup.select(sel)
        if links:
            break

    seen = set()
    for a in links[:MAX_ARTICLES_PER_FEED]:
        title = a.get_text(strip=True)
        href = _make_absolute(a.get("href", ""), url)
        if href and href not in seen and title:
            seen.add(href)
            articles.append({"title": title, "url": href, "summary": "", "published": "", "source": "NIST"})

    logger.info(f"NIST: {len(articles)}개 수집")
    return articles


def scrape_treasury() -> list[dict]:
    """Treasury 보도자료 — RSS 404 대체."""
    url = "https://home.treasury.gov/news/press-releases"
    soup = _get_soup(url)
    if not soup:
        return []

    articles = []
    selectors = [
        "div.views-row h3 a",
        "article h2 a",
        "div.view-content a[href*='/press-release/']",
        "li.views-row a",
    ]
    links = []
    for sel in selectors:
        links = soup.select(sel)
        if links:
            break

    seen = set()
    for a in links[:MAX_ARTICLES_PER_FEED]:
        title = a.get_text(strip=True)
        href = _make_absolute(a.get("href", ""), url)
        if href and href not in seen and title:
            seen.add(href)
            articles.append({"title": title, "url": href, "summary": "", "published": "", "source": "Treasury"})

    logger.info(f"Treasury: {len(articles)}개 수집")
    return articles


def scrape_ftc() -> list[dict]:
    """FTC 보도자료 — RSS HTML 반환 대체."""
    url = "https://www.ftc.gov/news-events/news/press-releases"
    soup = _get_soup(url)
    if not soup:
        return []

    articles = []
    selectors = [
        "div.views-row h3 a",
        "article h2 a",
        "div.view-content a[href*='/press-release']",
        "li.views-row a",
    ]
    links = []
    for sel in selectors:
        links = soup.select(sel)
        if links:
            break

    seen = set()
    for a in links[:MAX_ARTICLES_PER_FEED]:
        title = a.get_text(strip=True)
        href = _make_absolute(a.get("href", ""), url)
        if href and href not in seen and title:
            seen.add(href)
            articles.append({"title": title, "url": href, "summary": "", "published": "", "source": "FTC"})

    logger.info(f"FTC: {len(articles)}개 수집")
    return articles


def collect_scraped() -> list[dict]:
    all_articles = []
    for func in (scrape_ustr, scrape_nist, scrape_treasury, scrape_ftc):
        try:
            all_articles.extend(func())
        except Exception as e:
            logger.error(f"스크래퍼 오류 [{func.__name__}]: {e}")
    return all_articles
