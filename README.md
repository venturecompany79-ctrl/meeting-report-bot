# Meeting Report Bot

영업 미팅 후 Google Drive에 업로드된 회의록(.txt 또는 .pdf)과 회사 소개서(.pdf)를
자동으로 분석하여 컨설팅 진단 보고서(.docx)를 생성하는 봇입니다.

## 워크플로우

1. 영업사원이 Drive `inbox/날짜_회사명/` 폴더에 `meeting.txt` 또는 `meeting.pdf`와 `company.pdf` 업로드
2. GitHub Actions가 매시간 폴링
3. Gemini로 보고서 생성 → .docx 변환
4. `done/` 폴더로 결과물 이동
5. 완료 메일 발송 + Notion `Meeting-bot` 페이지에 하위 서브페이지 생성

## 기술 스택

- Google Drive API (Service Account 인증)
- Gemini 2.5 Pro (LLM)
- python-docx (보고서 생성)
- Notion API (보고서 아카이브)
- GitHub Actions (스케줄링)

## Google Drive 연동 설정 (1회)

1. Google Cloud Console에서 service account를 생성하고 JSON 키 다운로드 (이 repo의 `service-account.json` 형식)
2. Drive의 `inbox`, `processing`, `done`, `error` 폴더 4개 각각에 service account 이메일을 **Editor** 권한으로 공유
3. GitHub repo Settings → Secrets and variables → Actions에 `SERVICE_ACCOUNT_JSON` 추가 — JSON 파일 내용 전체를 그대로 붙여넣기

Service account 인증은 7일 만료가 없어 OAuth 갱신 작업이 불필요합니다.

## Notion 연동 설정 (1회)

1. https://www.notion.so/profile/integrations 에서 internal integration 생성 → secret 복사
2. Notion에서 `Meeting-bot` 페이지를 열고 우측 상단 `...` → `Connections` → 위에서 만든 integration 연결
3. GitHub repo Settings → Secrets and variables → Actions에 추가:
   - `NOTION_TOKEN` = integration secret
   - `NOTION_PARENT_PAGE_ID` = `Meeting-bot` 페이지의 32자 ID (URL 마지막 부분)

`NOTION_PARENT_PAGE_ID`가 비어 있으면 Notion 단계는 건너뜁니다 (보고서·메일은 정상 동작).
