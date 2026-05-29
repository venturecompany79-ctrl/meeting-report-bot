"""보고서 JSON(dict) → Notion 블록(JSON) 변환.

원본 meeting-report-bot 의 notion_client.py 렌더링 로직을 이식.
구글 드라이브 관련(파일 임베드/북마크) 부분은 제거하고, 보고서 본문만 생성한다.
지원 컴포넌트: h2/h3, paragraph, bullets, numbered, lead_in_bullets, table, kpi_strip, callout.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

MAX_TEXT_LEN = 2000  # Notion rich_text content 최대 길이


def _rt(text: Any, *, bold: bool = False, color: str = "default") -> Dict[str, Any]:
    s = str(text or "")[:MAX_TEXT_LEN]
    elem: Dict[str, Any] = {"type": "text", "text": {"content": s}}
    if bold:
        elem["annotations"] = {"bold": True}
    if color != "default":
        elem.setdefault("annotations", {})["color"] = color
    return elem


def _para(text: str) -> Dict[str, Any]:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [_rt(text)]}}


def _heading(level: int, text: str) -> Dict[str, Any]:
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {"rich_text": [_rt(text)]}}


def _bullet(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [_rt(text)]},
    }


def _lead_bullet(lead: str, rest: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [_rt(f"{lead} — ", bold=True), _rt(rest)]},
    }


def _numbered(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": [_rt(text)]},
    }


def _callout(label: str, text: str) -> Dict[str, Any]:
    body = f"{label}\n\n{text}" if label else text
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [_rt(body)],
            "icon": {"type": "emoji", "emoji": "💡"},
            "color": "blue_background",
        },
    }


def _divider() -> Dict[str, Any]:
    return {"object": "block", "type": "divider", "divider": {}}


def _table(headers: List[str], rows: List[List[str]]) -> Optional[Dict[str, Any]]:
    if not headers:
        return None
    width = len(headers)

    def row(cells: List[str]) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": [[_rt(cells[i] if i < len(cells) else "")] for i in range(width)]
            },
        }

    children = [row(headers)] + [row(r) for r in rows]
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": children,
        },
    }


def _component_blocks(comp: Dict[str, Any]) -> List[Dict[str, Any]]:
    ctype = comp.get("type", "paragraph")

    if ctype == "h2":
        return [_heading(2, comp.get("text", ""))]
    if ctype == "h3":
        return [_heading(3, comp.get("text", ""))]
    if ctype == "paragraph":
        return [_para(comp.get("text", ""))]
    if ctype == "bullets":
        return [_bullet(i) for i in comp.get("items", [])]
    if ctype == "numbered":
        return [_numbered(i) for i in comp.get("items", [])]
    if ctype == "lead_in_bullets":
        out: List[Dict[str, Any]] = []
        for item in comp.get("items", []):
            if isinstance(item, dict):
                out.append(_lead_bullet(item.get("lead", ""), item.get("rest", "")))
            else:
                out.append(_bullet(str(item)))
        return out
    if ctype == "table":
        tbl = _table(comp.get("headers", []), comp.get("rows", []))
        return [tbl] if tbl else []
    if ctype == "kpi_strip":
        items = comp.get("items", [])
        headers = [i.get("label", "") for i in items]
        values = [i.get("value", "") for i in items]
        tbl = _table(headers, [values])
        return [tbl] if tbl else []
    if ctype == "callout":
        return [_callout(comp.get("label", ""), comp.get("text", ""))]

    return [_para(str(comp))]


def _section_blocks(section: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    title = section.get("title", "")
    eyebrow = section.get("eyebrow", "")
    if title or eyebrow:
        heading_text = f"{eyebrow} — {title}" if eyebrow and title else (title or eyebrow)
        blocks.append(_heading(2, heading_text))
    intro = section.get("intro")
    if intro:
        blocks.append(_para(intro))
    for comp in section.get("components", []):
        blocks.extend(_component_blocks(comp))
    return blocks


def build_report_blocks(report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """보고서 JSON 을 Notion 블록 시퀀스로 평탄화."""
    blocks: List[Dict[str, Any]] = []

    # Executive summary
    exec_summary = report_data.get("executive_summary")
    if exec_summary:
        blocks.extend(
            _section_blocks(
                {
                    "eyebrow": exec_summary.get("eyebrow", "EXECUTIVE SUMMARY"),
                    "title": exec_summary.get("title", ""),
                    "intro": exec_summary.get("intro", ""),
                    "components": [],
                }
            )
        )
        kpi = exec_summary.get("kpi") or []
        if kpi:
            blocks.extend(_component_blocks({"type": "kpi_strip", "items": kpi}))
        if exec_summary.get("key_takeaway"):
            blocks.append(_callout("KEY TAKEAWAY", exec_summary["key_takeaway"]))

    # Meta table
    meta = report_data.get("meta_table") or []
    if meta:
        blocks.append(_heading(2, "보고서 정보"))
        tbl = _table(["항목", "내용"], meta)
        if tbl:
            blocks.append(tbl)

    blocks.append(_divider())

    # Main sections
    for section in report_data.get("sections", []) or []:
        blocks.extend(_section_blocks(section))

    # Closing
    closing = report_data.get("closing")
    if closing:
        blocks.extend(_section_blocks(closing))

    return blocks
