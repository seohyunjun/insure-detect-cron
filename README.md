# 국민연금 가입 사업장 API 변경 감지

국민연금 가입 사업장 공공데이터 API 문서의 변경 사항을 자동으로 감지하고 Slack으로 알림을 전송하는 모니터링 도구입니다.

## 기능

- API 문서(OpenAPI/Swagger) 변경 자동 감지
- 변경 내용 분석 (엔드포인트 추가/삭제, 스키마 변경, 버전 변경)
- Slack 웹훅을 통한 실시간 알림
- GitHub Actions를 통한 자동 스케줄 실행 (매일 오전 9시 KST)

## 모니터링 대상

- **API**: [국민연금 가입 사업장 내역](https://www.data.go.kr/data/15083277/openapi.do)
- **문서 URL**: https://infuser.odcloud.kr/oas/docs?namespace=15083277/v1

## 설치

### 요구 사항

- Python 3.11+

### 의존성 설치

```bash
pip install -r requirements.txt
```

## 설정

### 환경 변수

`.env.example`을 참고하여 `.env` 파일을 생성합니다:

```bash
cp .env.example .env
```

`.env` 파일에 Slack 웹훅 URL을 설정합니다:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### GitHub Actions 설정

GitHub 저장소의 Settings > Secrets and variables > Actions에서 다음 시크릿을 추가합니다:

- `SLACK_WEBHOOK_URL`: Slack 웹훅 URL

## 사용법

### 수동 실행

```bash
python check_api_changes.py
```

### 자동 실행

GitHub Actions 워크플로우가 매일 오전 9시(KST)에 자동으로 실행됩니다.

수동으로 워크플로우를 실행하려면 GitHub 저장소의 Actions 탭에서 "Check API Changes" 워크플로우를 선택하고 "Run workflow"를 클릭합니다.

## 알림 내용

변경이 감지되면 다음 정보가 Slack으로 전송됩니다:

- 추가/삭제된 API 엔드포인트
- 추가/삭제된 데이터 스키마
- API 버전 변경

## 파일 구조

```
.
├── check_api_changes.py    # 메인 스크립트
├── requirements.txt        # Python 의존성
├── .env.example           # 환경 변수 예시
├── .github/
│   └── workflows/
│       └── check-api-changes.yml  # GitHub Actions 워크플로우
└── last_state.json        # API 상태 저장 파일 (자동 생성)
```

## 라이선스

MIT
