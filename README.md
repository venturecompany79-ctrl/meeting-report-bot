# 미팅 리포트 봇 (Notion 전용)

[venturecompany79-ctrl/meeting-report-bot](https://github.com/venturecompany79-ctrl/meeting-report-bot)
을 **Google Drive 없이 Notion 안에서 모든 것을 처리**하도록 재구성한 버전입니다.

원본은 영업사원이 Google Drive `inbox/` 폴더에 회의록·회사소개서를 올리면 GitHub Actions가
폴링 → Gemini로 보고서 생성 → `.docx` → Drive `done/` + Notion 서브페이지 + 메일이었습니다.

이 버전은 Drive/메일을 제거하고, **Notion 테이블에 파일을 업로드하면** 봇이 새 row를 감지하여
보고서를 만들고 **같은 row의 페이지에 보고서를 작성**합니다. 보고서 내용(프롬프트·디자인 시스템·
JSON 구조)과 Gemini 사용은 원본을 그대로 따릅니다.

```
[Notion 테이블 row]
  회사정보(파일) + 회의록(파일) + 상태=미처리
        │  (주기적 폴링)
        ▼
  파일 다운로드 → 텍스트 추출(PDF/DOCX/TXT)
        │
        ▼
  Gemini 2.5 → 컨설팅 진단 보고서 JSON (executive summary / sections / SWOT / 로드맵 / closing)
        │
        ▼
  row 페이지 본문에 보고서 블록(표·KPI·콜아웃 포함) 작성
  (옵션) 디자인된 .docx 생성 → '보고서' 파일 컬럼에 첨부
  상태=완료 + 보고서생성일 기록
```

## 1. 테이블 구조

봇은 다음 컬럼(속성)을 사용합니다. 이름은 `.env` 로 바꿀 수 있습니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| 이름 | 제목(title) | row 제목 (회사명/미팅명 등) |
| 회사정보 | 파일(files) | 회사 소개서/사업자등록증 등 (PDF/DOCX/TXT) |
| 회의록 | 파일(files) | 미팅 녹취록/회의록 (PDF/DOCX/TXT) |
| 상태 | 선택(select) | `미처리` / `처리중` / `완료` / `오류` |
| 보고서생성일 | 날짜(date) | 완료 시 자동 기록 |
| 보고서 | 파일(files) | (옵션) 생성된 `.docx` 자동 첨부 |
| 오류메시지 | 텍스트(rich_text) | 실패 시 사유 기록 |

> 봇은 **상태 = 미처리** 이고 회사정보·회의록 파일이 **모두 첨부된** row 만 처리합니다.
> 처리 중에는 `처리중`으로 바꿔 중복 처리를 막고, 끝나면 `완료`/`오류`로 표시합니다.

## 2. 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 값 채우기
```

## 3. Notion 준비

1. https://www.notion.so/profile/integrations 에서 **내부 통합(Integration)** 생성 → 토큰을 `.env` 의 `NOTION_TOKEN` 에 입력.
2. 테이블을 둘 **부모 페이지**를 만들고, 페이지 우측 상단 `···` → **연결(Connections)** 에서 위 Integration 을 추가(공유).
3. 부모 페이지 URL 끝의 32자리 hex 가 페이지 ID 입니다.

### 테이블 자동 생성 (권장)

```bash
python scripts/setup_database.py <부모페이지ID>
```

출력된 `NOTION_DATABASE_ID` 를 `.env` 에 넣으세요. (직접 만든 테이블을 쓰려면 위 컬럼 구조를
맞추고 Integration 과 공유한 뒤 그 database id 를 넣으면 됩니다.)

## 4. 실행

```bash
python -m src.main --once   # 미처리 row 1회 처리 후 종료 (테스트용)
python -m src.main          # 폴링 루프 (POLL_INTERVAL_SECONDS 간격)
```

상시 운영은 `launchd`(macOS)/`systemd`/cron/컨테이너 등으로 `python -m src.main` 프로세스를
띄워 두거나, `--once` 를 cron 에 등록하면 됩니다. (원본의 GitHub Actions 시간당 폴링과 동일한 개념)

## 5. 설정 (.env)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NOTION_TOKEN` | — | Notion Integration 토큰 |
| `NOTION_DATABASE_ID` | — | 대상 테이블 ID |
| `GEMINI_API_KEY` | — | Google AI Studio API 키 |
| `GEMINI_MODEL` | `gemini-2.5-flash` | 보고서 생성 모델 (무료 티어는 `pro` 불가 → `flash`) |
| `ATTACH_DOCX` | `true` | 생성한 `.docx` 를 '보고서' 컬럼에 첨부할지 |
| `POLL_INTERVAL_SECONDS` | `60` | 폴링 간격(초) |
| `PROP_*` / `STATUS_*` | (위 표) | 컬럼명/상태값 커스터마이징 |

## 6. 보고서 형식 변경

- `templates/report.md` — 보고서 섹션 구조/체크리스트 (원본 템플릿)
- `templates/design.md` — 색상·타이포·컴포넌트 등 디자인 시스템 (`.docx` 스타일 + 프롬프트 주입)
- `src/llm.py` — Gemini 프롬프트 및 출력 JSON 스펙

보고서는 JSON(cover/executive_summary/meta_table/sections/closing)으로 생성되어, Notion
블록(표·KPI 스트립·콜아웃·lead-in 불릿 등)과 `.docx` 양쪽으로 렌더링됩니다.

## 7. 지원 파일 형식

`.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.json` (구형 `.doc` 는 미지원 → `.docx`/`.pdf` 로 저장).
스캔본 PDF 는 텍스트 추출이 안 될 수 있습니다.

## 8. 원본 대비 변경 요약

| | 원본 | 이 버전 |
|---|------|---------|
| 입력 | Google Drive `inbox/` 폴더 | Notion 테이블 파일 컬럼 |
| 트리거 | GitHub Actions 매시간 폴링 | 로컬/서버 주기 폴링 (`--once` 도 가능) |
| LLM | Gemini 2.5 | 동일 (Gemini 2.5) |
| 보고서 본문 | Notion 서브페이지 | 업로드한 row 의 페이지 본문 |
| `.docx` | Drive `done/` 저장 + 외부링크 | (옵션) Notion 파일 컬럼에 직접 첨부 |
| 메일 | 완료 메일 발송 | 제거 (Notion 상태로 대체) |
| Google Drive | 필수 | **제거** |

## 파일 구성

```
src/
  config.py        환경 변수 설정
  notion_api.py    Notion API (조회/다운로드/블록추가/파일업로드/상태)
  extract.py       파일 텍스트 추출 (pdf/docx/txt, 한글 인코딩 자동)
  llm.py           Gemini 보고서 생성 (원본 프롬프트 이식)
  report.py        보고서 JSON → Notion 블록 변환 (원본 로직 이식)
  docx_builder.py  디자인 시스템 기반 .docx 생성 (원본)
  main.py          폴링 루프 / row 처리 오케스트레이션
templates/
  report.md        보고서 구조 템플릿 (원본)
  design.md        디자인 시스템 (원본)
scripts/
  setup_database.py  Notion 테이블 자동 생성
```
