import os, json, re
from google import genai

def load_template(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'templates', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_report(meeting_text, company_text):
    api_key = os.environ['GEMINI_API_KEY']
    client = genai.Client(api_key=api_key)

    report_template = load_template('report.md')
    design_guide = load_template('design.md')

    prompt = f"""당신은 venturecompany의 시니어 컨설턴트이자 보고서 디자이너입니다.

미팅 녹취록과 회사 소개서를 분석하여, 아래 디자인 시스템과 보고서 템플릿에 따라
구조화된 JSON 보고서를 생성해주세요.

# 디자인 시스템
{design_guide}

# 보고서 템플릿
{report_template}

# 미팅 녹취록
{meeting_text}

# 회사 소개서
{company_text}

---

# 출력 규칙

아래 형식의 JSON으로만 응답하세요. 다른 설명, 마크다운 코드블록(```), 주석은 절대 금지.

{{
  "cover": {{
    "company_name": "고객사명",
    "subtitle": "1차 미팅 기반 사전 진단",
    "prepared_for": "고객사 대표/담당자",
    "prepared_by": "venturecompany",
    "date": "YYYY.MM.DD"
  }},
  "meta_table": [
    ["고객사명", "(주)○○○○"],
    ["미팅 일자", "YYYY.MM.DD"],
    ["보고서 작성일", "YYYY.MM.DD"],
    ["작성자", "○○○ 컨설턴트"],
    ["문서 버전", "v1.0"]
  ],
  "sections": [
    {{
      "eyebrow": "EXECUTIVE SUMMARY",
      "title": "회사 개요",
      "intro": "1~2문장 섹션 도입부",
      "components": [
        {{
          "type": "table",
          "headers": ["구분", "내용"],
          "rows": [
            ["법인명", "(주)○○○○"],
            ["대표이사", "○○○"]
          ]
        }},
        {{
          "type": "bullets",
          "items": ["항목 1", "항목 2"]
        }},
        {{
          "type": "lead_in_bullets",
          "items": [
            {{"lead": "주력 제품", "rest": "설명"}},
            {{"lead": "업종", "rest": "설명"}}
          ]
        }},
        {{
          "type": "kpi_strip",
          "items": [
            {{"value": "30%", "label": "법인세 절감"}},
            {{"value": "5억원", "label": "정부지원금 확보"}},
            {{"value": "12개월", "label": "추진 기간"}}
          ]
        }},
        {{
          "type": "callout",
          "label": "KEY TAKEAWAY",
          "text": "전략적 시사점 한두 문장"
        }},
        {{
          "type": "numbered",
          "items": ["첫 번째", "두 번째", "세 번째"]
        }},
        {{
          "type": "paragraph",
          "text": "일반 본문 단락"
        }}
      ]
    }}
  ],
  "closing": {{
    "eyebrow": "CLOSING PERSPECTIVE",
    "title": "다음 단계",
    "intro": "마무리 도입부",
    "components": []
  }}
}}

# 작성 원칙

1. **report.md의 `[USE: ✅/❌]` 처리**: 
   - 미팅에서 정보가 확보된 섹션만 포함 (해당 섹션을 sections 배열에 추가)
   - 정보가 없는 섹션은 통째로 제외
   - `[필수]` 섹션(회사 개요, 미팅 핵심 요약, 다음 단계)은 반드시 포함

2. **컴포넌트 타입 사용**:
   - `table`: 항목/내용 등 정형화된 정보
   - `bullets`: 단순 목록
   - `lead_in_bullets`: "용어 — 설명" 구조
   - `kpi_strip`: 정량 지표 3개 (반드시 3개여야 함)
   - `callout`: 핵심 시사점 강조 (KEY TAKEAWAY, STRATEGIC READ, IMPLICATION 등)
   - `numbered`: 순서가 있는 항목
   - `paragraph`: 일반 단락

3. **eyebrow는 영문 대문자**: SECTION 01, SECTION 02, EXECUTIVE SUMMARY 형식

4. **각 섹션 구조**:
   - eyebrow → title(H1) → intro(짧은 도입 1~2문장) → components

5. **톤**: 3인칭, 단정형, 근거 기반. 추측은 명시.

6. **callout 박스**는 섹션당 최대 1~2개

7. **KPI 스트립**은 반드시 3개 항목 (정보 없으면 사용하지 말 것)

8. **빈 표 행 금지**: 정보가 없는 행은 제외

9. **고객사명, 날짜 등**은 미팅 녹취록과 회사 소개서에서 추출. 없으면 "(미확인)" 표기

10. report.md의 `[필수]` 섹션은 반드시 다음 순서로:
    1) 회사 개요 (EXECUTIVE SUMMARY)
    2) 미팅 핵심 요약 (SECTION 01)
    3) 그 외 정보 있는 [선택] 섹션들 (SECTION 02, 03...)
    4) 다음 단계 (CLOSING PERSPECTIVE)

JSON만 출력하세요. ```json 같은 마크다운 코드블록도 사용하지 마세요.
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    raw = response.text.strip()

    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 파싱 실패: {e}")
        print(f"--- Gemini 응답 (처음 500자) ---")
        print(raw[:500])
        print(f"--- 끝 ---")
        return {
            "cover": {
                "company_name": "(파싱 실패)",
                "subtitle": "보고서 생성 오류",
                "prepared_for": "-",
                "prepared_by": "venturecompany",
                "date": "-"
            },
            "meta_table": [],
            "sections": [{
                "eyebrow": "ERROR",
                "title": "보고서 생성 실패",
                "intro": "Gemini 응답을 JSON으로 파싱하지 못했습니다.",
                "components": [{"type": "paragraph", "text": raw}]
            }],
            "closing": None
        }
