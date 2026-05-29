"""미팅 리포트용 Notion 데이터베이스(테이블)를 자동 생성.

사전 준비:
  1) https://www.notion.so/my-integrations 에서 Integration 생성 → NOTION_TOKEN 설정
  2) 데이터베이스를 만들 부모 '페이지'를 Notion 에서 만들고, 그 페이지의 '연결(Connections)'에
     위 Integration 을 추가 (공유)
  3) 부모 페이지 URL 끝의 32자리 hex 가 PAGE_ID

사용법:
  python scripts/setup_database.py <부모페이지ID>

생성 후 출력되는 database id 를 .env 의 NOTION_DATABASE_ID 에 넣으세요.
(이 스크립트는 ANTHROPIC_API_KEY 없이도 동작합니다.)
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def env(key: str, default: str) -> str:
    return os.getenv(key, default)


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python scripts/setup_database.py <부모페이지ID>")
        sys.exit(1)

    token = os.getenv("NOTION_TOKEN")
    if not token:
        print("NOTION_TOKEN 환경 변수가 필요합니다 (.env 확인).")
        sys.exit(1)

    parent_page_id = sys.argv[1].replace("-", "")

    prop_company = env("PROP_COMPANY", "회사정보")
    prop_meeting = env("PROP_MEETING", "회의록")
    prop_status = env("PROP_STATUS", "상태")
    prop_report_date = env("PROP_REPORT_DATE", "보고서생성일")
    prop_report_file = env("PROP_REPORT_FILE", "보고서")
    prop_error = env("PROP_ERROR", "오류메시지")
    s_pending = env("STATUS_PENDING", "미처리")
    s_processing = env("STATUS_PROCESSING", "처리중")
    s_done = env("STATUS_DONE", "완료")
    s_error = env("STATUS_ERROR", "오류")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    body = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "미팅 리포트"}}],
        "properties": {
            "이름": {"title": {}},
            prop_company: {"files": {}},
            prop_meeting: {"files": {}},
            prop_status: {
                "select": {
                    "options": [
                        {"name": s_pending, "color": "gray"},
                        {"name": s_processing, "color": "yellow"},
                        {"name": s_done, "color": "green"},
                        {"name": s_error, "color": "red"},
                    ]
                }
            },
            prop_report_date: {"date": {}},
            prop_report_file: {"files": {}},
            prop_error: {"rich_text": {}},
        },
    }

    resp = requests.post(f"{API}/databases", headers=headers, json=body, timeout=60)
    if resp.status_code >= 400:
        print(f"실패 {resp.status_code}: {resp.text}")
        sys.exit(1)

    db = resp.json()
    db_id = db["id"]
    print("데이터베이스 생성 완료!")
    print(f"  database id : {db_id}")
    print(f"  url         : {db.get('url')}")
    print()
    print("아래 값을 .env 에 설정하세요:")
    print(f"  NOTION_DATABASE_ID={db_id.replace('-', '')}")
    print()
    print(f"새 row 추가 후 '{prop_status}' 컬럼을 '{s_pending}' 로 두면 봇이 자동 처리합니다.")


if __name__ == "__main__":
    main()
