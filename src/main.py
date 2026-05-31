"""미팅 리포트 봇 진입점 (Notion 전용).

Notion 데이터베이스를 주기적으로 폴링하여, '미처리' 상태이며 회사정보/회의록
파일이 첨부된 row 를 찾아 Gemini 로 컨설팅 진단 보고서를 생성하고
해당 row 페이지 본문에 작성한다. (옵션) 디자인된 .docx 를 '보고서' 파일 컬럼에 첨부.

사용법:
    python -m src.main          # 폴링 루프 (기본)
    python -m src.main --once   # 한 번만 처리하고 종료
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
import re
import traceback
from datetime import date
from typing import Any, Dict

from .config import config
from .docx_builder import build_docx
from .extract import extract_text
from .llm import generate_report
from .notion_api import NotionAPI
from .report import build_report_blocks

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def _collect_text(notion: NotionAPI, page: Dict[str, Any], prop: str) -> str:
    entries = notion.file_entries(page, prop)
    if not entries:
        raise ValueError(f"'{prop}' 컬럼에 첨부된 파일이 없습니다.")
    texts = []
    for name, url in entries:
        _log(f"  · 다운로드/추출: {name}")
        data = notion.download(url)
        texts.append(extract_text(name, data))
    return "\n\n".join(texts)


def _safe_filename(name: str) -> str:
    """파일명에 쓸 수 없는 문자 제거 (한글·괄호 등은 유지)."""
    name = re.sub(r'[\\/:*?"<>|\n\r\t]+', "", (name or "")).strip().strip(".")
    return name or "보고서"


def _report_filename(title: str) -> str:
    """리포트 파일명: '회사명_생성일(YYMMDD).docx'  (예: (주)엘레트라_260529.docx)"""
    return f"{_safe_filename(title)}_{date.today().strftime('%y%m%d')}.docx"


def _attach_docx(
    notion: NotionAPI, schema: Dict[str, str], page_id: str, report_data: Dict[str, Any], filename: str
) -> None:
    """디자인된 .docx 를 생성해 '보고서' files 속성에 첨부 (옵션)."""
    if config.PROP_REPORT_FILE not in schema or schema[config.PROP_REPORT_FILE] != "files":
        _log(f"  · '{config.PROP_REPORT_FILE}' files 컬럼이 없어 docx 첨부 건너뜀")
        return
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, filename)
        build_docx(report_data, path)
        with open(path, "rb") as f:
            data = f.read()
    _log(f"  · docx 업로드 중... ({filename})")
    upload_id = notion.upload_file(filename, data, _DOCX_MIME)
    notion.update_properties(
        page_id,
        {config.PROP_REPORT_FILE: notion.file_upload_property(upload_id, filename)},
    )


def process_page(notion: NotionAPI, schema: Dict[str, str], page: Dict[str, Any]) -> None:
    page_id = page["id"]
    title = notion.title_text(page) or "(제목 없음)"
    status_type = schema.get(config.PROP_STATUS, "select")
    _log(f"처리 시작: {title} ({page_id})")

    # 1) 처리중으로 표시 (중복 처리 방지)
    notion.update_properties(
        page_id,
        {config.PROP_STATUS: notion.status_value(status_type, config.STATUS_PROCESSING)},
    )

    try:
        company_text = _collect_text(notion, page, config.PROP_COMPANY)
        meeting_text = _collect_text(notion, page, config.PROP_MEETING)

        _log("  · Gemini 보고서 생성 중...")
        report_data = generate_report(
            config.GEMINI_API_KEY, config.GEMINI_MODEL, meeting_text, company_text
        )

        blocks = build_report_blocks(report_data)
        _log(f"  · Notion 페이지에 {len(blocks)}개 블록 작성")
        notion.append_blocks(page_id, blocks)

        # (옵션) 디자인된 docx 첨부 — 파일명: 회사명_생성일(YYMMDD).docx
        if config.ATTACH_DOCX:
            try:
                _attach_docx(notion, schema, page_id, report_data, _report_filename(title))
            except Exception as de:  # noqa: BLE001
                _log(f"  · docx 첨부 실패(무시): {de}")

        # 완료 표시 + 생성일 기록
        props: Dict[str, Any] = {
            config.PROP_STATUS: notion.status_value(status_type, config.STATUS_DONE)
        }
        if schema.get(config.PROP_REPORT_DATE) == "date":
            props[config.PROP_REPORT_DATE] = {"date": {"start": date.today().isoformat()}}
        notion.update_properties(page_id, props)
        _log(f"완료: {title}")

    except Exception as exc:  # noqa: BLE001
        _log(f"오류: {title} -> {exc}")
        traceback.print_exc()
        err_props: Dict[str, Any] = {
            config.PROP_STATUS: notion.status_value(status_type, config.STATUS_ERROR)
        }
        if schema.get(config.PROP_ERROR) == "rich_text":
            err_props[config.PROP_ERROR] = {
                "rich_text": [{"type": "text", "text": {"content": str(exc)[:1900]}}]
            }
        try:
            notion.update_properties(page_id, err_props)
        except Exception:  # noqa: BLE001
            pass


def run_once(notion: NotionAPI) -> int:
    schema = notion.property_types(config.NOTION_DATABASE_ID)
    status_type = schema.get(config.PROP_STATUS, "select")
    pages = notion.query_unprocessed(
        config.NOTION_DATABASE_ID,
        config.PROP_STATUS,
        status_type,
        config.STATUS_PENDING,
        config.PROP_COMPANY,
        config.PROP_MEETING,
    )
    if not pages:
        _log("처리할 미처리 row 없음.")
        return 0
    _log(f"미처리 row {len(pages)}건 발견.")
    for page in pages:
        process_page(notion, schema, page)
    return len(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description="Notion 미팅 리포트 봇")
    parser.add_argument("--once", action="store_true", help="한 번만 처리하고 종료")
    args = parser.parse_args()

    notion = NotionAPI(config.NOTION_TOKEN, config.NOTION_VERSION)

    if args.once:
        run_once(notion)
        return

    _log(f"폴링 시작 (간격 {config.POLL_INTERVAL_SECONDS}s). 중지하려면 Ctrl+C.")
    while True:
        try:
            run_once(notion)
        except Exception as exc:  # noqa: BLE001
            _log(f"루프 오류: {exc}")
            traceback.print_exc()
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
