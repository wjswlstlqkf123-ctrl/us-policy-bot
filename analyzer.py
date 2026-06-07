import anthropic
import logging
from config import ANTHROPIC_API_KEY, MODEL, KEYWORDS

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Cached system prompt — stays in cache across multiple article analyses in the same session
SYSTEM_PROMPT = """당신은 미국 정책 뉴스를 한국어로 요약하는 전문 분석가입니다.
미국의 금융·경제·기술 정책이 한국 경제와 기업에 미치는 영향을 정확하게 분석합니다.
전문 용어는 한국어 표준 금융/경제 용어를 사용하고, 간결하고 명확하게 응답해주세요."""


def classify_article(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    scores = {cat: sum(1 for w in words if w in text) for cat, words in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "경제"


def analyze_article(title: str, url: str, summary: str, source: str, published: str) -> dict | None:
    category = classify_article(title, summary)
    content_text = f"제목: {title}\n출처: {source}\n날짜: {published}\n내용: {summary[:800] if summary else '(본문 없음)'}"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"""다음 미국 정책 뉴스를 분석해주세요:

{content_text}

아래 형식을 정확히 지켜 응답하세요:

[한국어 제목]
(원문 제목을 자연스러운 한국어로 번역)

[3줄 요약]
1. (첫 번째 핵심 내용)
2. (두 번째 핵심 내용)
3. (세 번째 핵심 내용)

[한국 영향]
(한국 경제/기업에 미치는 영향 1-2문장)""",
                }
            ],
        )

        raw = response.content[0].text.strip()
        korean_title, summary_text, impact = _parse_response(raw, title)

        return {
            "category": category,
            "korean_title": korean_title,
            "summary": summary_text,
            "korea_impact": impact,
            "url": url,
            "source": source,
            "published": published,
        }

    except anthropic.RateLimitError:
        logger.warning(f"API 속도 제한 — 기사 건너뜀: {title[:60]}")
    except anthropic.APIError as e:
        logger.error(f"Anthropic API 오류: {e}")
    except Exception as e:
        logger.error(f"분석 실패 [{title[:60]}]: {e}")

    return None


def _parse_response(text: str, fallback_title: str) -> tuple[str, str, str]:
    korean_title = fallback_title
    summary_items: list[str] = []
    impact_parts: list[str] = []
    current = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if "[한국어 제목]" in line:
            current = "title"
        elif "[3줄 요약]" in line:
            current = "summary"
        elif "[한국 영향]" in line:
            current = "impact"
        elif current == "title":
            korean_title = line
            current = None  # capture only the first line after header
        elif current == "summary" and line and line[0].isdigit():
            summary_items.append(line)
        elif current == "impact":
            impact_parts.append(line)

    return (
        korean_title,
        "\n".join(summary_items) or "요약 정보 없음",
        " ".join(impact_parts).strip() or "영향 분석 정보 없음",
    )
