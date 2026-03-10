# App Store Review Monitor

앱스토어 리뷰를 6시간마다 자동 수집하고, 중요도/카테고리 분류 후 Slack으로 알림을 보냅니다.

## 구조

```
├── .github/workflows/check-reviews.yml  ← 6시간마다 자동 실행
├── scripts/
│   ├── check_reviews.py                 ← 리뷰 수집 (RSS Feed)
│   ├── format_mail.py                   ← 중요도/카테고리 분류
│   └── send_mail.py                     ← Slack Webhook 발송
├── main.py                              ← 전체 파이프라인 실행
├── config.example.yml                   ← 설정 템플릿
└── requirements.txt
```

## 설정 방법

### 1. Slack Incoming Webhook 만들기

1. https://api.slack.com/apps → Create New App → From scratch
2. Incoming Webhooks → 활성화(On)
3. Add New Webhook to Workspace → 알림 받을 채널 선택
4. 생성된 URL 복사

### 2. GitHub Secrets 등록

Repository > Settings > Secrets and variables > Actions:

| Secret | 설명 | 예시 |
|--------|------|------|
| `SLACK_WEBHOOK_URL` | Slack Webhook URL | `https://hooks.slack.com/services/T.../B.../xxx` |
| `APP_IDS` | 앱스토어 앱 ID (쉼표 구분) | `123456789,987654321` |
| `APP_NAMES` | 앱 이름 (쉼표 구분) | `MyApp,MyOtherApp` |
| `APP_COUNTRIES` | 모니터링할 국가 (쉼표 구분) | `kr,us` |

### 3. 앱 ID 확인 방법

앱스토어에서 앱 페이지 URL의 `id` 뒤 숫자:
```
https://apps.apple.com/kr/app/my-app/id123456789
                                       ^^^^^^^^^
```

## 로컬 테스트

```bash
pip install -r requirements.txt

export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T.../B.../xxx"
export APP_IDS="123456789,987654321"
export APP_NAMES="MyApp,MyOtherApp"
export APP_COUNTRIES="kr,us"

python main.py
```

## 수동 실행

GitHub > Actions > "Check App Store Reviews" > Run workflow 버튼으로 즉시 실행 가능.
