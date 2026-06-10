import asyncio
import logging
import time

from collectors.rss import collect_rss
from collectors.scraper import collect_scraped
from analyzer import analyze_article, classify_article
from notifier import notify_article
from db import init_db, is_first_run, is_sent, mark_sent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CHECK_INTERVAL = 300  # 5분 (초)
API_CALL_DELAY = 2    # Claude API 호출 간 딜레이 (초)


_PLACEHOLDER = {"요약 정보 없음", "영향 분석 정보 없음"}

def _is_valid(result: dict) -> bool:
    """제목·날짜·요약·영향 분석이 모두 실질적인 내용을 가질 때만 True."""
    title_ok = bool(result.get("korean_title", "").strip())
    date_ok = bool(result.get("published", "").strip())
    summary_ok = result.get("summary", "") not in _PLACEHOLDER and len(result.get("summary", "")) > 10
    impact_ok = result.get("korea_impact", "") not in _PLACEHOLDER and len(result.get("korea_impact", "")) > 10
    return title_ok and date_ok and summary_ok and impact_ok


def run_pipeline():
    """동기 함수로 유지 — notifier 내부의 asyncio.run()과 충돌 방지를 위해
    monitor_loop에서 asyncio.to_thread()로 호출됩니다."""
    logger.info("=== 파이프라인 시작 ===")

    rss_articles = collect_rss()
    scraped_articles = collect_scraped()
    all_articles = rss_articles + scraped_articles
    logger.info(f"총 수집: {len(all_articles)}개 (RSS {len(rss_articles)} + 스크래핑 {len(scraped_articles)})")

    # 첫 실행: 기존 기사를 모두 DB에만 기록하고 전송하지 않음
    if is_first_run():
        seeded = 0
        for article in all_articles:
            url = article.get("url", "").strip()
            if url:
                mark_sent(url, article["title"])
                seeded += 1
        logger.info(f"첫 실행 감지 — 기존 기사 {seeded}개 DB 등록 완료 (전송 생략). 다음 주기부터 신규 기사만 전송합니다.")
        return

    sent_count = 0
    skipped_count = 0

    for article in all_articles:
        url = article.get("url", "").strip()
        if not url:
            continue

        if is_sent(url):
            skipped_count += 1
            continue

        # 날짜 없는 기사 스킵
        if not article.get("published", "").strip():
            mark_sent(url, article["title"])
            logger.info(f"날짜 없음 스킵: {article['title'][:60]}")
            continue

        # 5개 카테고리 외 일반 정치 뉴스는 API 호출 없이 스킵
        if classify_article(article["title"], article.get("summary", ""), article.get("source", "")) is None:
            mark_sent(url, article["title"])
            logger.info(f"관련 없음 스킵: {article['title'][:60]}")
            continue

        result = analyze_article(
            title=article["title"],
            url=url,
            summary=article.get("summary", ""),
            source=article.get("source", ""),
            published=article.get("published", ""),
        )

        if result and _is_valid(result):
            notify_article(result)
            mark_sent(url, article["title"])
            sent_count += 1
            logger.info(f"전송 완료: [{result['category']}] {article['title'][:60]}")
            time.sleep(API_CALL_DELAY)
        elif result:
            # 날짜 누락 또는 내용 미달 — DB에만 기록해 재시도 방지
            mark_sent(url, article["title"])
            reason = "날짜 없음" if not result.get("published", "").strip() else "내용 미달"
            logger.info(f"발송 제외 [{reason}]: {article['title'][:60]}")

    logger.info(f"=== 파이프라인 완료 — 신규 전송: {sent_count}개 / 중복 스킵: {skipped_count}개 ===")


async def monitor_loop():
    init_db()
    logger.info(f"실시간 모니터링 시작 — {CHECK_INTERVAL // 60}분 간격으로 체크합니다.")

    while True:
        try:
            # 블로킹 pipeline을 스레드에서 실행해 이벤트 루프를 블로킹하지 않음
            await asyncio.to_thread(run_pipeline)
        except Exception as e:
            logger.error(f"파이프라인 오류 (계속 실행): {e}", exc_info=True)

        logger.info(f"다음 체크까지 {CHECK_INTERVAL // 60}분 대기…")
        await asyncio.sleep(CHECK_INTERVAL)


def main():
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        logger.info("봇 종료")


if __name__ == "__main__":
    main()
