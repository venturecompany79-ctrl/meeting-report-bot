"""
Notion integration — creates a sub-page under the configured parent page
containing the docx file embed, the Drive folder link, and the rendered
report body.
"""
import os
import requests

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Notion API limit on children per create/append request
MAX_CHILDREN_PER_REQUEST = 100
# Notion rich_text content max length is 2000 chars
MAX_TEXT_LEN = 2000


def _headers():
    token = os.environ["NOTION_TOKEN"]
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _rt(text, *, bold=False, color="default"):
    """Build a single rich_text element, truncated to API limit."""
    s = str(text or "")[:MAX_TEXT_LEN]
    annotations = {"bold": bold} if bold else {}
    elem = {"type": "text", "text": {"content": s}}
    if annotations:
        elem["annotations"] = annotations
    if color != "default":
        elem.setdefault("annotations", {})["color"] = color
    return elem


def _para(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [_rt(text)]},
    }


def _heading(level, text):
    key = f"heading_{level}"
    return {
        "object": "block",
        "type": key,
        key: {"rich_text": [_rt(text)]},
    }


def _bullet(text):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [_rt(text)]},
    }


def _lead_bullet(lead, rest):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [
                _rt(f"{lead} — ", bold=True),
                _rt(rest),
            ]
        },
    }


def _numbered(text):
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": [_rt(text)]},
    }


def _callout(label, text):
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


def _divider():
    return {"object": "block", "type": "divider", "divider": {}}


def _table(headers, rows):
    """Notion table block — returns a single block with table_row children."""
    if not headers:
        return None
    width = len(headers)

    def row(cells):
        return {
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": [
                    [_rt(cells[i] if i < len(cells) else "")]
                    for i in range(width)
                ]
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


def _component_blocks(comp):
    """Convert a docx_builder-style component dict to one or more Notion blocks."""
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
        out = []
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
        # Render as a single-row 3-column table
        items = comp.get("items", [])
        headers = [i.get("label", "") for i in items]
        values = [i.get("value", "") for i in items]
        tbl = _table(headers, [values])
        return [tbl] if tbl else []
    if ctype == "callout":
        return [_callout(comp.get("label", ""), comp.get("text", ""))]

    return [_para(str(comp))]


def _section_blocks(section):
    blocks = []
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


def _build_report_blocks(report_data):
    """Flatten the report JSON into a sequence of Notion blocks."""
    blocks = []

    # Executive summary
    exec_summary = report_data.get("executive_summary")
    if exec_summary:
        blocks.extend(_section_blocks({
            "eyebrow": exec_summary.get("eyebrow", "EXECUTIVE SUMMARY"),
            "title": exec_summary.get("title", ""),
            "intro": exec_summary.get("intro", ""),
            "components": [],
        }))
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

    # Main sections
    for section in report_data.get("sections", []) or []:
        blocks.extend(_section_blocks(section))

    # Closing
    closing = report_data.get("closing")
    if closing:
        blocks.extend(_section_blocks(closing))

    return blocks


def _build_header_blocks(drive_folder_url, docx_external_url, docx_filename):
    """Top-of-page blocks: file embed + Drive link + divider."""
    blocks = []
    if docx_external_url:
        blocks.append({
            "object": "block",
            "type": "file",
            "file": {
                "type": "external",
                "external": {"url": docx_external_url},
                "name": docx_filename,
            },
        })
    if drive_folder_url:
        blocks.append({
            "object": "block",
            "type": "bookmark",
            "bookmark": {"url": drive_folder_url},
        })
    blocks.append(_divider())
    return blocks


def _create_page(parent_page_id, title, children):
    """POST /pages with up to 100 children."""
    body = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {
            "title": {"title": [_rt(title)]},
        },
        "children": children[:MAX_CHILDREN_PER_REQUEST],
    }
    r = requests.post(f"{API_BASE}/pages", headers=_headers(), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def _append_children(block_id, children):
    """PATCH /blocks/{id}/children, chunking by 100."""
    for i in range(0, len(children), MAX_CHILDREN_PER_REQUEST):
        chunk = children[i:i + MAX_CHILDREN_PER_REQUEST]
        r = requests.patch(
            f"{API_BASE}/blocks/{block_id}/children",
            headers=_headers(),
            json={"children": chunk},
            timeout=30,
        )
        r.raise_for_status()


def create_meeting_subpage(
    parent_page_id,
    meeting_name,
    drive_folder_url,
    docx_external_url,
    docx_filename,
    report_data,
):
    """Create a sub-page under parent_page_id and return its URL."""
    children = (
        _build_header_blocks(drive_folder_url, docx_external_url, docx_filename)
        + _build_report_blocks(report_data)
    )

    page = _create_page(parent_page_id, meeting_name, children)
    page_id = page["id"]

    if len(children) > MAX_CHILDREN_PER_REQUEST:
        _append_children(page_id, children[MAX_CHILDREN_PER_REQUEST:])

    return page.get("url", "")
