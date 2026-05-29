"""Notion REST API 래퍼.

- 데이터베이스(테이블) 스키마 조회
- '미처리' 상태이며 회사정보/회의록 파일이 모두 첨부된 row 조회
- 파일 속성에서 다운로드 URL 추출
- 페이지 본문에 보고서 블록 추가
- 상태 / 보고서생성일 / 오류메시지 속성 업데이트
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import requests

API = "https://api.notion.com/v1"


class NotionError(RuntimeError):
    pass


class NotionAPI:
    def __init__(self, token: str, version: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": version,
                "Content-Type": "application/json",
            }
        )

    # ---------- 내부 ----------
    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        resp = self.session.request(method, f"{API}{path}", timeout=60, **kwargs)
        if resp.status_code >= 400:
            raise NotionError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        return resp.json()

    # ---------- 스키마 ----------
    def get_database(self, database_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/databases/{database_id}")

    def property_types(self, database_id: str) -> Dict[str, str]:
        """{속성이름: 타입} 매핑을 반환."""
        db = self.get_database(database_id)
        return {name: prop["type"] for name, prop in db.get("properties", {}).items()}

    # ---------- 조회 ----------
    def query_unprocessed(
        self,
        database_id: str,
        status_prop: str,
        status_type: str,
        pending_value: str,
        company_prop: str,
        meeting_prop: str,
    ) -> List[Dict[str, Any]]:
        """처리 대상 row 목록.

        대상 조건: (상태 = '미처리') 또는 (상태 미설정/비어있음)  AND  회사정보·회의록 파일이 모두 첨부됨.
        → 새 row 에 상태를 따로 지정하지 않아도 파일만 올리면 자동 처리된다.
        (select 타입만 is_empty 지원. status 타입은 항상 값이 있으므로 equals 만 사용)
        """
        if status_type == "select":
            status_filter: Dict[str, Any] = {
                "or": [
                    {"property": status_prop, "select": {"equals": pending_value}},
                    {"property": status_prop, "select": {"is_empty": True}},
                ]
            }
        else:
            status_filter = {"property": status_prop, status_type: {"equals": pending_value}}
        filt = {
            "and": [
                status_filter,
                {"property": company_prop, "files": {"is_not_empty": True}},
                {"property": meeting_prop, "files": {"is_not_empty": True}},
            ]
        }
        results: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            body: Dict[str, Any] = {"filter": filt, "page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            data = self._request("POST", f"/databases/{database_id}/query", json=body)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return results

    # ---------- 파일 ----------
    @staticmethod
    def file_entries(page: Dict[str, Any], prop_name: str) -> List[Tuple[str, str]]:
        """파일 속성에서 (name, url) 목록을 추출."""
        prop = page.get("properties", {}).get(prop_name)
        if not prop or prop.get("type") != "files":
            return []
        out: List[Tuple[str, str]] = []
        for f in prop.get("files", []):
            name = f.get("name", "file")
            if f.get("type") == "file":
                url = f["file"]["url"]
            elif f.get("type") == "external":
                url = f["external"]["url"]
            else:
                continue
            out.append((name, url))
        return out

    @staticmethod
    def download(url: str) -> bytes:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp.content

    # ---------- 본문(블록) 추가 ----------
    def append_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> None:
        # Notion 은 한 번에 최대 100개 블록만 허용 → 청크 처리
        for i in range(0, len(blocks), 100):
            chunk = blocks[i : i + 100]
            self._request(
                "PATCH",
                f"/blocks/{page_id}/children",
                json={"children": chunk},
            )

    # ---------- 파일 업로드 (생성한 docx 첨부용) ----------
    def upload_file(self, filename: str, data: bytes, content_type: str) -> str:
        """Notion 파일 업로드 3단계 → file_upload id 반환.

        1) POST /file_uploads 로 업로드 슬롯 생성
        2) 반환된 upload_url 에 multipart/form-data 로 바이트 전송
        3) 호출 측에서 id 를 files 속성/블록에 첨부
        """
        created = self._request(
            "POST",
            "/file_uploads",
            json={"filename": filename, "content_type": content_type},
        )
        upload_id = created["id"]
        upload_url = created["upload_url"]

        # multipart 전송 — Content-Type 은 requests 가 boundary 와 함께 설정하도록 둔다
        headers = {
            "Authorization": self.session.headers["Authorization"],
            "Notion-Version": self.session.headers["Notion-Version"],
        }
        resp = requests.post(
            upload_url,
            headers=headers,
            files={"file": (filename, data, content_type)},
            timeout=120,
        )
        if resp.status_code >= 400:
            raise NotionError(f"파일 업로드 실패 {resp.status_code}: {resp.text}")
        return upload_id

    @staticmethod
    def file_upload_property(upload_id: str, name: str) -> Dict[str, Any]:
        """files 타입 속성에 업로드한 파일을 첨부하기 위한 페이로드."""
        return {
            "files": [
                {"type": "file_upload", "name": name, "file_upload": {"id": upload_id}}
            ]
        }

    # ---------- 속성 업데이트 ----------
    def update_properties(self, page_id: str, properties: Dict[str, Any]) -> None:
        self._request("PATCH", f"/pages/{page_id}", json={"properties": properties})

    @staticmethod
    def status_value(status_type: str, value: str) -> Dict[str, Any]:
        """select / status 타입에 맞는 속성 페이로드."""
        if status_type == "status":
            return {"status": {"name": value}}
        return {"select": {"name": value}}

    @staticmethod
    def title_text(page: Dict[str, Any]) -> str:
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                parts = [t.get("plain_text", "") for t in prop.get("title", [])]
                return "".join(parts).strip()
        return ""
