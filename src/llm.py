"""Gemini 기반 컨설팅 진단 보고서(JSON) 생성.

원본 meeting-report-bot 의 gemini_client.py 프롬프트/로직을 그대로 이식.
templates/report.md(보고서 구조) + templates/design.md(디자인 시스템) 을 프롬프트에 주입한다.
"""
from __future__ import annotations

import json
import os
import re

from google import genai

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _strip_markdown_bold(obj):
    """모든 문자열 값에서 ** 마크다운 볼드 마커 제거."""
    if isinstance(obj, str):
        return obj.replace("**", "")
    if isinstance(obj, dict):
        return {k: _strip_markdown_bold(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_markdown_bold(v) for v in obj]
    return obj


def _load_template(filename: str) -> str:
    path = os.path.join(_BASE, "templates", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_report(api_key: str, model: str, meeting_text: str, company_text: str) -> dict:
    client = genai.Client(api_key=api_key)

    report_template = _load_template("report.md")
    design_guide = _load_template("design.md")

    prompt = f"""당신은 venturecompany의 시니어 컨설턴트이자 전략 보고서 작성 전문가입니다.

미팅 녹취록과 회사 소개서를 분석하여, 매킨지/BCG 수준의 컨설팅 진단 보고서를 JSON으로 작성합니다.

# 디자인 시스템
{design_guide}

# 보고서 템플릿
{report_template}

# 미팅 녹취록
{meeting_text}

# 회사 소개서
{company_text}

---

# 보고서 작성 핵심 원칙

## 1. 분량 기준
- 목표 분량: 10~14페이지 분량의 깊이 있는 보고서
- 섹션 수: SECTION 01~13 수준의 풍부한 구성 (최소 8개 섹션)
- 각 컨설팅 제안: 1페이지 분량 (한두 줄로 끝내지 말 것)

## 2. 컨설팅 제안 섹션 구조 (필수 4블록)
모든 "컨설팅 제안" 섹션은 반드시 다음 4블록 포함:
1) 현황 진단 (h3 + lead_in_bullets 3~5개) — 구체적 사실, 수치, 시점 명시
2) 제안 내용 (h3 + bullets/numbered/table) — 구체적 액션, 우선순위 명시
3) 기대 효과 (h3 + bullets 3개 이상) — 정량적 효과 우선 (절감액, 금리 차이 등)
4) 예상 추진기간 (paragraph) — 명확한 기간 명시 (예: 약 4~6주)

## 3. 정량 지표 추출 의무
미팅 녹취록과 회사 소개서에서 모든 숫자를 빠짐없이 추출:
- 매출액, 차입금, 금리, 직원 수, 업력, 시효, 만기, 절감 금액 등

## 4. 시간 민감도 강조
시효, 데드라인이 있는 항목은 반드시 시급도 표기

## 5. EXECUTIVE SUMMARY 구성 (필수)
1) 미팅 일자/배경 한 문장
2) 회사 핵심 진단 한 문장
3) kpi_strip (3개 핵심 지표)
4) callout (KEY TAKEAWAY) — 핵심 시사점 + Quick-Win 권고

## 6. 회사 식별 정보 정확성
회사명, 미팅 일자, 컨설턴트 이름을 녹취록에서 추출. 추출 불가 시에만 "(미확인)"

## 7. 톤
매킨지/BCG 스타일: 단정형, 근거 기반, "권고", "필수", "즉시" 등 단정 표현

---

# 출력 JSON 스펙

{{
  "cover": {{
    "company_name": "(주)○○ 식품",
    "subtitle": "1차 미팅 기반 사전 진단",
    "volume": "VOLUME 01",
    "prepared_for": "(주)○○ 식품 대표이사",
    "prepared_by": "venturecompany | 김지선 컨설턴트",
    "date": "2026.04.30"
  }},
  "executive_summary": {{
    "eyebrow": "EXECUTIVE SUMMARY",
    "title": "1차 미팅 사전 진단 요약",
    "intro": "본 보고서는 ...",
    "kpi": [
      {{"value": "50억", "label": "2025년 매출"}},
      {{"value": "6건", "label": "핵심 Pain Point"}},
      {{"value": "4건", "label": "Quick-Win"}}
    ],
    "key_takeaway": "1차 미팅에서 식별된 ..."
  }},
  "meta_table": [
    ["고객사명", "..."],
    ["미팅 일자", "..."],
    ["보고서 작성일", "..."],
    ["작성자", "..."],
    ["문서 버전", "v1.0"]
  ],
  "sections": [
    {{
      "eyebrow": "SECTION 01",
      "title": "회사 개요",
      "intro": "...",
      "components": [
        {{"type": "h3", "text": "1.1 기본 정보"}},
        {{"type": "table", "headers": ["구분", "내용"], "rows": [...]}},
        {{"type": "h3", "text": "1.2 사업 영역"}},
        {{"type": "lead_in_bullets", "items": [...]}}
      ]
    }},
    {{
      "eyebrow": "SECTION 02",
      "title": "미팅 핵심 요약",
      "intro": "...",
      "components": [
        {{"type": "h3", "text": "2.1 대표님 주요 관심사 (Pain Points)"}},
        {{"type": "numbered", "items": ["Pain Point 1 — 상세", "Pain Point 2 — 상세"]}},
        {{"type": "h3", "text": "2.2 회사 현황 진단 요약"}},
        {{"type": "lead_in_bullets", "items": [
          {{"lead": "성장 단계", "rest": "..."}},
          {{"lead": "시급도가 높은 이슈", "rest": "..."}},
          {{"lead": "컨설팅 추진 방향", "rest": "..."}}
        ]}}
      ]
    }},
    {{
      "eyebrow": "SECTION XX",
      "title": "컨설팅 제안: [영역]",
      "intro": "...",
      "components": [
        {{"type": "h3", "text": "현황 진단"}},
        {{"type": "lead_in_bullets", "items": [...]}},
        {{"type": "h3", "text": "제안 내용"}},
        {{"type": "table", "headers": [...], "rows": [...]}},
        {{"type": "h3", "text": "기대 효과"}},
        {{"type": "bullets", "items": ["정량적 효과 1", "정량적 효과 2"]}},
        {{"type": "paragraph", "text": "예상 추진기간: 약 4~6주."}}
      ]
    }},
    {{
      "eyebrow": "SECTION XX",
      "title": "SWOT 분석",
      "intro": "...",
      "components": [
        {{"type": "table", "headers": ["구분", "내용"], "rows": [
          ["Strength", "..."],
          ["Weakness", "..."],
          ["Opportunity", "..."],
          ["Threat", "..."]
        ]}}
      ]
    }},
    {{
      "eyebrow": "SECTION XX",
      "title": "실행 로드맵",
      "intro": "...",
      "components": [
        {{"type": "h3", "text": "[1개월]"}},
        {{"type": "bullets", "items": [...]}},
        {{"type": "h3", "text": "[2-3개월]"}},
        {{"type": "bullets", "items": [...]}},
        {{"type": "h3", "text": "[4-6개월]"}},
        {{"type": "bullets", "items": [...]}},
        {{"type": "h3", "text": "우선 추진 과제 (Quick-Win)"}},
        {{"type": "table", "headers": ["순위", "과제", "예상기간", "기대 효과"], "rows": [...]}}
      ]
    }}
  ],
  "closing": {{
    "eyebrow": "CLOSING PERSPECTIVE",
    "title": "전략적 종합 의견",
    "intro": "...",
    "components": [
      {{"type": "callout", "label": "STRATEGIC READ", "text": "본 사업은 ..."}}
    ]
  }}
}}

# 절대 지킬 것

1. 각 컨설팅 제안 섹션은 반드시 4블록(현황진단/제안내용/기대효과/추진기간) 모두 포함
2. 컨설팅 제안 섹션은 최소 4개 이상
3. 표(table)를 적극 활용
4. 모든 숫자 추출
5. Quick-Win 표 필수 (실행 로드맵 섹션에 포함)
6. SWOT 섹션 필수
7. EXECUTIVE SUMMARY에 KPI 스트립 + KEY TAKEAWAY 콜아웃 필수
8. CLOSING PERSPECTIVE에 STRATEGIC READ 콜아웃 필수
9. JSON만 출력. 코드블록(```), 주석, 설명 일체 금지

미팅 녹취록을 깊이 분석하여 위 모든 원칙을 준수한 컨설팅 진단 보고서 JSON을 출력하세요.
"""

    response = client.models.generate_content(model=model, contents=prompt)
    return _parse_report_json(response.text)


def generate_summary(api_key: str, model: str, report_data: dict) -> dict:
    """전체 보고서 JSON 을 5페이지 분량의 핵심 요약본 JSON 으로 압축."""
    client = genai.Client(api_key=api_key)
    full_json = json.dumps(report_data, ensure_ascii=False)

    prompt = f"""아래는 전체 컨설팅 진단 보고서 JSON 입니다. 이를 **5페이지 분량의 핵심 요약본**으로 압축하세요.

# 전체 보고서 JSON
{full_json}

# 요약본 작성 원칙
- 분량: 약 5페이지 (전체 10~14페이지의 절반 수준)
- 동일한 출력 JSON 스펙 사용: cover / executive_summary / meta_table / sections / closing
- 컴포넌트 타입도 동일하게 사용 가능: h3, paragraph, bullets, numbered, lead_in_bullets, table, kpi_strip, callout
- 섹션(sections)은 **가장 핵심적인 3~5개로 추리고**, 각 섹션은 간결하게 (표는 핵심 행만 유지)
- EXECUTIVE SUMMARY(kpi_strip + KEY TAKEAWAY 콜아웃)는 반드시 포함
- 컨설팅 제안은 핵심 1~2개만, 각 제안은 '제안/기대효과' 위주로 압축
- CLOSING PERSPECTIVE(STRATEGIC READ 콜아웃) 포함
- cover 의 company_name/prepared_for/prepared_by/date 는 원본 그대로 유지하되,
  cover.subtitle 은 "핵심 요약본 (5p)" 로 설정
- 사실/수치는 원본 보고서에 있는 것만 사용 (새로 지어내지 말 것)
- JSON만 출력. 코드블록(```), 주석, 설명 일체 금지

위 보고서를 5페이지 핵심 요약본 JSON 으로 출력하세요.
"""
    response = client.models.generate_content(model=model, contents=prompt)
    return _parse_report_json(response.text)


def _parse_report_json(text: str) -> dict:
    """Gemini 응답 텍스트에서 보고서 JSON 을 파싱 (코드펜스 제거 + 볼드 마커 제거)."""
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        return _strip_markdown_bold(json.loads(raw))
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 파싱 실패: {e}")
        print("--- Gemini 응답 (처음 800자) ---")
        print(raw[:800])
        print("--- 끝 ---")
        return {
            "cover": {
                "company_name": "(파싱 실패)",
                "subtitle": "오류",
                "prepared_for": "-",
                "prepared_by": "venturecompany",
                "date": "-",
            },
            "meta_table": [],
            "sections": [
                {
                    "eyebrow": "ERROR",
                    "title": "보고서 생성 실패",
                    "intro": "JSON 파싱 실패",
                    "components": [{"type": "paragraph", "text": raw[:3000]}],
                }
            ],
            "closing": None,
        }
