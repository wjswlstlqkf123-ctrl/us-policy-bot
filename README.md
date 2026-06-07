# 미국 정책 모니터링 텔레그램 봇

미국의 금융·경제·기술 분야 정책 뉴스를 자동 수집하고, Claude AI로 한국어 요약 후 텔레그램으로 전송하는 봇입니다.

## 수집 출처

| 출처 | 방식 | 분야 |
|------|------|------|
| Federal Reserve | RSS | 금융 |
| SEC | RSS | 금융 |
| US Treasury | RSS | 금융/경제 |
| White House | RSS | 전체 |
| FTC | RSS | 기술/경제 |
| Reuters Politics | RSS | 전체 |
| USTR | 스크래핑 | 경제 |
| NIST | 스크래핑 | 기술 |
| White House OSTP | 스크래핑 | 기술 |

## 사전 준비

### 1. API 키 발급

**Anthropic API 키**
1. [Anthropic Console](https://console.anthropic.com) 접속
2. 회원가입 후 API Keys 메뉴에서 키 발급

**텔레그램 봇 토큰**
1. 텔레그램에서 `@BotFather` 검색 후 대화 시작
2. `/newbot` 명령어 입력 → 봇 이름과 username 설정
3. 발급된 토큰 복사

**텔레그램 Chat ID**
1. 생성한 봇에게 아무 메시지 전송
2. 브라우저에서 아래 URL 접속 (TOKEN 부분 교체):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. 응답 JSON의 `result[0].message.chat.id` 값 복사

### 2. 환경 설정

```bash
# 프로젝트 디렉토리 이동
cd us-policy-bot

# .env 파일 생성
copy .env.example .env
```

`.env` 파일을 열어 실제 값으로 수정:

```
ANTHROPIC_API_KEY=sk-ant-실제키입력
TELEGRAM_TOKEN=실제봇토큰입력
TELEGRAM_CHAT_ID=실제채팅ID입력
```

## 설치 방법

```bash
# Python 3.11 이상 권장

# 가상환경 생성 (선택사항, 권장)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 패키지 설치
pip install -r requirements.txt
```

## 실행 방법

```bash
python main.py
```

- 실행 즉시 1회 수집·분석·전송 후, 매일 **오전 9시 / 오후 6시 (KST)** 자동 실행됩니다.
- `Ctrl+C`로 종료합니다.

## 텔레그램 메시지 예시

```
🏦 [금융정책]

제목: 연준, 기준금리 0.25%p 인상 결정

📋 요약
1. 연방준비제도이사회가 FOMC 회의에서 금리를 5.25~5.50%로 인상
2. 인플레이션 목표 2% 달성을 위한 긴축 기조 유지
3. 추가 인상 가능성은 경제 데이터에 따라 결정될 예정

🇰🇷 한국 영향
한미 금리 역전폭 확대로 외국인 자금 유출 압력이 높아질 수 있으며, 한국은행의 금리 결정에도 영향을 미칠 전망입니다.

🔗 https://www.federalreserve.gov/...
📅 2025-01-01T00:00:00Z
```

## 프로젝트 구조

```
us-policy-bot/
├── main.py          # 스케줄러 및 파이프라인 진입점
├── config.py        # 환경변수 및 상수
├── analyzer.py      # Claude API 요약 분석
├── notifier.py      # 텔레그램 전송
├── db.py            # SQLite 중복 방지 DB
├── collectors/
│   ├── rss.py       # RSS 피드 수집
│   └── scraper.py   # 웹 스크래핑
├── requirements.txt
├── .env.example
└── README.md
```

## 로그 확인

실행 시 콘솔에 아래 형식으로 로그가 출력됩니다:

```
2025-01-01 09:00:00 [INFO] __main__ — === 파이프라인 시작 ===
2025-01-01 09:00:05 [INFO] __main__ — 총 수집: 42개 (RSS 35 + 스크래핑 7)
2025-01-01 09:00:08 [INFO] __main__ — 전송 완료: [금융] Federal Reserve Announces...
2025-01-01 09:00:10 [INFO] __main__ — === 파이프라인 완료 — 신규 전송: 3개 / 중복 스킵: 39개 ===
```

## 주의사항

- 정부 사이트 스크래핑은 웹사이트 구조 변경 시 동작하지 않을 수 있습니다. RSS 기반 수집은 안정적으로 동작합니다.
- `claude-haiku-4-5` 모델 사용으로 비용을 최소화하며, 프롬프트 캐싱이 적용됩니다.
- 이미 전송된 기사는 `us_policy_bot.db`에 저장되어 재전송되지 않습니다.
