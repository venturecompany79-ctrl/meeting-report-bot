# Meeting Report Bot — 새 환경 셋업 지침서

이 문서는 새 노트북·새 Claude 세션이 본 봇을 처음부터 셋업해 GitHub Actions 스케줄로 자동 운영할 수 있도록 설계됐습니다. 사용자 본인이 직접 처리해야 하는 GUI 단계(브라우저 로그인, 결제 등록 등)는 명확히 표기합니다.

---

## 0. 봇 개요

- **목적**: Google Drive의 `inbox` 폴더에 업로드된 미팅 자료(회의록 + 회사 소개서)로 컨설팅 진단 보고서(.docx)를 자동 생성
- **스케줄**: GitHub Actions cron `0 * * * *` (매시간)
- **결과물**: 보고서 .docx → Drive `done`, Notion 서브페이지, 완료 메일
- **언어**: Python 3.11
- **인증**: Google OAuth 2.0 user credentials (service account 아님 — `storageQuotaExceeded` 사유)

---

## 1. 사전 준비물

사용자가 가지고 있어야 하는 자격증명·접근 권한:

| 항목 | 어디서 받음 | 비고 |
|---|---|---|
| GitHub 계정 + 본 repo write 권한 | https://github.com/venturecompany79-ctrl/meeting-report-bot | repo 소유자 |
| Google 계정 (`venturecompany79@gmail.com` 또는 동등) | — | 이 계정에 `js-consulting-495208` 프로젝트가 있어야 함 |
| Google Cloud `credentials.json` | Cloud Console → APIs & Services → Credentials | OAuth client ID (Desktop app) |
| Gemini API key | https://aistudio.google.com | Free tier로 시작 가능 |
| Gmail 앱 비밀번호 | Google 계정 보안 → 앱 비밀번호 | 2단계 인증 필수 |
| Notion 통합 (선택) | https://www.notion.so/profile/integrations | Meeting-bot 페이지 연결 |
| Drive 폴더 4개 ID | Drive에서 만들어 URL 마지막 32자 복사 | inbox/processing/done/error |

---

## 2. 새 노트북 로컬 셋업

Claude 세션이 진행 가능한 부분.

```bash
git clone https://github.com/venturecompany79-ctrl/meeting-report-bot.git
cd meeting-report-bot
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 검증: 테스트 통과 확인
```bash
venv/bin/python3 -m unittest tests.test_main_logic -v
```
`OK`가 출력되면 코드 베이스는 정상.

---

## 3. credentials.json / token.json 배치

이 두 파일은 `.gitignore`에 등록돼 있어 repo에 없습니다. 새 노트북에 별도로 가져와야 합니다.

### credentials.json
- 기존 노트북에서 복사하거나
- Cloud Console에서 OAuth Client(Desktop)를 새로 만들어 다운로드 → repo 루트에 `credentials.json`으로 저장

### token.json 발급 (브라우저 동의 필요)
```bash
venv/bin/python3 auth_setup.py
```
브라우저가 열리지 않으면 `_auth_oneshot.py` 패턴 사용:
```python
# 임시 파일 _auth_oneshot.py
import webbrowser
_orig = webbrowser.open
def _patched(url, *a, **k):
    print(f"\n>>> OAUTH URL: {url}\n", flush=True)
    return _orig(url, *a, **k)
webbrowser.open = _patched

from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/drive']
flow = InstalledAppFlow.from_client_secrets_file('./credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
with open('./token.json', 'w') as f:
    f.write(creds.to_json())
```
```bash
venv/bin/python3 -u _auth_oneshot.py
```
출력된 URL을 브라우저에서 열어 동의 → `token.json` 생성됨.

> ⚠️ **중요**: OAuth consent screen이 "Testing" 상태면 token이 7일마다 만료됩니다. 다음 절을 반드시 처리하세요.

---

## 4. OAuth 앱 Publish (영구화) — **사용자 GUI 작업**

이 단계를 생략하면 매주 token 재발급 작업을 반복해야 합니다.

1. https://console.cloud.google.com/apis/credentials/consent 열기
2. 우상단 프로젝트 선택기에서 **`js-consulting-495208`** 선택
   - 안 보이면 조직 드롭다운에서 "조직 없음(No organization)" 또는 다른 Google 계정으로 전환
3. **PUBLISH APP** 버튼 클릭
4. sensitive scope (`drive`) 경고 → 확인 (본인용은 verification 없이도 100명 한도로 동작)

Publish 후에는 token 만료 없이 무기한 동작합니다.

---

## 5. GitHub Secrets 등록 — **사용자 GUI 작업**

https://github.com/venturecompany79-ctrl/meeting-report-bot/settings/secrets/actions

| Secret 이름 | 값 |
|---|---|
| `TOKEN_JSON` | `token.json` 전체 내용 (한 줄 JSON) |
| `GEMINI_API_KEY` | AI Studio API 키 |
| `GEMINI_MODEL` | (선택) `gemini-2.5-pro` 쓰려면 billing 활성화 + 등록. 기본은 flash |
| `INBOX_FOLDER_ID` | Drive inbox 폴더 ID |
| `PROCESSING_FOLDER_ID` | Drive processing 폴더 ID |
| `DONE_FOLDER_ID` | Drive done 폴더 ID |
| `ERROR_FOLDER_ID` | Drive error 폴더 ID |
| `GMAIL_USER` | 알림용 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (코드가 자동으로 공백·NBSP 제거) |
| `NOTION_TOKEN` | (선택) Internal integration secret |
| `NOTION_PARENT_PAGE_ID` | (선택) Meeting-bot 페이지 32자 ID |

`token.json` 클립보드 복사:
```bash
pbcopy < token.json
```

---

## 6. Notion 통합 (선택)

1. https://www.notion.so/profile/integrations → internal integration 생성
2. 대상 노션 페이지(예: "Meeting-bot") → `...` → Connections → 만든 integration 추가
3. 페이지 URL 마지막 32자 → `NOTION_PARENT_PAGE_ID` secret 등록
4. integration secret → `NOTION_TOKEN` secret 등록

미설정 시 노션 단계는 자동 스킵, 봇 나머지는 정상 동작합니다.

---

## 7. 검증

GitHub Actions UI에서 수동 실행:

https://github.com/venturecompany79-ctrl/meeting-report-bot/actions/workflows/poll.yml → **Run workflow**

inbox에 `meeting.txt(또는 .pdf) + company.pdf`가 든 서브폴더가 있으면 처리되어야 합니다.

성공 시 로그:
```
▶ 처리 시작: 폴더명
  📥 파일 다운로드 중...
  📄 파일 파싱 중...
  🤖 Gemini 보고서 생성 중...
  📝 .docx 생성 중...
  📤 Drive 업로드 중...
  📝 Notion 페이지 생성 중...
✅ 메일 발송 완료
✅ 완료
```

---

## 8. 트러블슈팅 (이 봇이 실제로 부딪힌 함정들)

| 증상 | 원인 | 해결 |
|---|---|---|
| `invalid_grant: Token has been expired or revoked` | OAuth consent screen이 Testing 상태 → 7일 만료 | 4절 PUBLISH 처리 + 6절 token 재발급 |
| `Service Accounts do not have storage quota` | 개인 Gmail의 My Drive에는 service account 파일 생성 불가 | OAuth 방식 유지 (이 repo의 결론). Workspace 보유자만 Shared Drive 우회 가능 |
| `429 RESOURCE_EXHAUSTED ... limit: 0, model: gemini-2.5-pro` | Free tier에서 Pro 모델 자체 차단 | 기본 `gemini-2.5-flash` 사용. Pro 원하면 billing 활성화 + `GEMINI_MODEL` secret |
| `JSONDecodeError ... line 7 column 3` (service account secret) | Multi-line JSON이 YAML/env 경로에서 변형 | base64 인코딩 후 single-line secret으로 우회 |
| `UnicodeEncodeError: 'ascii' codec ... \xa0` (Gmail) | App password에 NBSP가 섞임 (브라우저 복사 결과) | 코드가 이미 모든 공백·NBSP 제거 후 인증 |
| `ValueError: PDF에서 텍스트를 추출할 수 없습니다` | 스캔본 PDF (이미지) | 텍스트 기반 PDF로 재 export. OCR 통합은 미구현 |
| `TabError: inconsistent use of tabs and spaces` | 들여쓰기 혼용 | 에디터에서 spaces로 통일 |
| Workflow가 실행 안 됨 (Actions 페이지에 새 run 없음) | cron disabled 또는 repo activity 부족 | Actions 탭에서 워크플로우 재활성화 |
| `inbox 그대로 남음` 출력 없이 종료 | inbox 안에 서브폴더가 없거나, 폴더 안에 `meeting.txt/pdf` + `company.pdf` 둘 다 없음 | 폴더 구조와 파일명 확인 |

---

## 9. 운영 흐름 (정상 사용)

새 미팅 발생 시:
1. Drive `inbox` 안에 새 서브폴더 생성 (예: `20260615_고객사명`)
2. 폴더 안에 `meeting.txt` 또는 `meeting.pdf` (회의록), `company.pdf` (회사 소개서) 업로드
3. 다음 정각 cron이 자동으로 처리 — `done`으로 이동, Notion 갱신, 메일 도착
4. 즉시 실행하려면 Actions에서 **Run workflow**

에러 발생 시:
- `error` 폴더에 폴더가 이동되고 `error.log` 파일이 함께 남음
- 메일·Notion 실패는 폴더가 `done`에 그대로 유지됨 (보고서 자체는 성공)

---

## 10. 코드 구조 (수정 위치)

```
.github/workflows/poll.yml    스케줄·env 정의
src/
  main.py                     진입점 (폴더 순회 / 상태 전이 / 호출 순서)
  drive_client.py             OAuth 인증 + Drive CRUD
  file_parser.py              read_txt, extract_pdf_text
  gemini_client.py            프롬프트 조립 + JSON 파싱 + ** 제거
  docx_builder.py             python-docx 렌더링 (디자인 시스템)
  notion_client.py            Notion REST API 직접 호출
  mailer.py                   Gmail SMTP
templates/
  design.md, report.md        Gemini 프롬프트에 주입되는 디자인·구조 명세
tests/test_main_logic.py      meeting.txt/pdf 경로 단위 테스트
auth_setup.py                 초기 OAuth 발급 스크립트
```

프롬프트·디자인 조정은 `templates/`만 수정해도 됩니다.

---

## 11. 새 Claude 세션 사용 시 권장 프롬프트

새 노트북에서 Claude Code를 띄우고 첫 메시지로:

> "이 repo의 `docs/setup-guide.md`를 읽고 새 환경에 셋업해줘. credentials.json은 [내가 어디서 가져올 위치]에 있어. Drive 폴더 ID와 Gemini API 키 등 외부 자격증명은 내가 직접 GitHub Secret에 등록할 거니까 그 단계 직전까지 진행해줘."

Claude는 2·3절(clone, venv, 의존성 설치, 검증)을 자동으로 수행하고, 4·5절은 사용자 GUI 작업이 필요하므로 안내·대기합니다.
