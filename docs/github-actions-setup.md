# GitHub Actions 무인 운영 설정

내 컴퓨터가 꺼져 있어도 GitHub 클라우드에서 봇이 주기적으로 돌도록 설정합니다.
워크플로우는 [`.github/workflows/poll.yml`](../.github/workflows/poll.yml) 에 이미 포함돼 있습니다.

## 동작 방식
- 15분마다 (cron `*/15 * * * *`) GitHub 가 `python -m src.main --once` 를 실행
- '미처리' row 가 있으면 보고서 생성 → Notion 작성, 없으면 즉시 종료
- 비밀키는 코드가 아닌 **GitHub Secrets** 에 저장 (`.env` 는 커밋되지 않음)

> ⚠️ GitHub Actions cron 은 최소 5분 간격이며, 부하에 따라 수 분 지연될 수 있습니다.
> "파일 업로드 후 몇 분 내 처리"는 되지만 실시간은 아닙니다.

## 1. 코드를 GitHub 에 올리기

로컬 폴더는 이미 git 으로 초기화되어 있습니다(첫 커밋 완료). 원격만 연결해 푸시하세요.

### A. 새 저장소에 올리는 경우
```bash
cd /Users/junsera/Documents/06_AI_PROJECT/04_JS_Meeting_Report_bot
# GitHub 웹에서 빈 저장소 생성 후 (예: meeting-report-bot-notion)
git remote add origin https://github.com/<계정>/<저장소>.git
git push -u origin main
```

### B. 기존 meeting-report-bot 저장소를 이 버전으로 교체하는 경우
```bash
git remote add origin https://github.com/venturecompany79-ctrl/meeting-report-bot.git
git push -u origin main --force   # 기존 내용을 이 Notion 버전으로 덮어씀 (주의)
```
> 기존 Drive 버전을 보존하고 싶으면 새 브랜치로 푸시하거나(A)안 추천.

## 2. Secrets 등록

GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|------|-----|
| `NOTION_TOKEN` | Notion 통합 토큰 (`.env` 의 값) |
| `NOTION_DATABASE_ID` | `36f67e678c5981958176f5ca459f30f4` |
| `GEMINI_API_KEY` | Gemini API 키 |

(선택) **Variables** 탭에서 `GEMINI_MODEL`, `ATTACH_DOCX` 를 추가하면 모델/동작을 바꿀 수 있습니다. 없으면 기본값(`gemini-2.5-flash`, `true`)이 쓰입니다.

## 3. 동작 확인
- 저장소 **Actions** 탭 → `meeting-report-bot poll` → **Run workflow** 로 수동 실행
- 로그에서 `미처리 row N건 발견` / `완료` 확인
- 이후로는 15분마다 자동 실행

## 무료 한도 주의
| 저장소 유형 | Actions 무료 한도 | 15분 주기 적합성 |
|-------------|-------------------|------------------|
| **Public** | 무제한 | ✅ 문제 없음 |
| **Private** | 월 2,000분 | ⚠️ 15분 주기면 한도 초과 가능 → 주기를 30~60분으로 늘리거나 Public 권장 |

주기 변경: `.github/workflows/poll.yml` 의 `cron` 수정
- 매 30분: `*/30 * * * *`
- 매시간: `0 * * * *`

## Gemini 무료 티어 주의
- `gemini-2.5-pro` 는 무료 티어 사용 불가 → `gemini-2.5-flash` 사용 (현재 기본값)
- 분당/일일 요청 한도가 있어, row 가 많으면 일부가 한도(429)에 걸려 `오류` 처리될 수 있음
  → 다음 실행에서 해당 row 의 `상태` 를 `미처리` 로 되돌리면 재처리됩니다
