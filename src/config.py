"""환경 변수 기반 설정."""
import os

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"환경 변수 {key} 가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return val


def _bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


class Config:
    # Notion
    NOTION_TOKEN = _require("NOTION_TOKEN")
    NOTION_DATABASE_ID = _require("NOTION_DATABASE_ID")
    NOTION_VERSION = "2022-06-28"

    # LLM (Claude) — 인증은 SDK 가 환경에서 자동 해석
    # (GitHub Actions: Workload Identity Federation / 로컬: ANTHROPIC_API_KEY 또는 `ant auth login`)
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")

    # 컬럼(속성) 이름
    PROP_COMPANY = os.getenv("PROP_COMPANY", "회사정보")
    PROP_MEETING = os.getenv("PROP_MEETING", "회의록")
    PROP_STATUS = os.getenv("PROP_STATUS", "상태")
    PROP_REPORT_DATE = os.getenv("PROP_REPORT_DATE", "보고서생성일")
    PROP_REPORT_FILE = os.getenv("PROP_REPORT_FILE", "보고서")
    PROP_REPORT_SUMMARY = os.getenv("PROP_REPORT_SUMMARY", "보고서요약")
    PROP_ERROR = os.getenv("PROP_ERROR", "오류메시지")

    # 상태 값
    STATUS_PENDING = os.getenv("STATUS_PENDING", "미처리")
    STATUS_PROCESSING = os.getenv("STATUS_PROCESSING", "처리중")
    STATUS_DONE = os.getenv("STATUS_DONE", "완료")
    STATUS_ERROR = os.getenv("STATUS_ERROR", "오류")

    # 동작
    ATTACH_DOCX = _bool("ATTACH_DOCX", True)
    POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))


config = Config()
