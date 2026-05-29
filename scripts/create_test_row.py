"""파이프라인 테스트용: 샘플 회사정보/회의록 파일을 업로드한 row 를 생성."""
import sys

sys.path.insert(0, ".")
from src.config import config  # noqa: E402
from src.notion_api import NotionAPI  # noqa: E402

COMPANY = """\
(주)그린바이트 회사 소개서

- 법인명: 주식회사 그린바이트 (GreenByte Inc.)
- 대표이사: 김도윤
- 법인설립일: 2021년 3월 2일
- 본점 소재지: 경기도 성남시 분당구 판교로 242
- 자본금: 5억원
- 임직원 수: 23명 (연구개발 인력 9명)
- 주요 사업: AI 기반 식품 품질검사 솔루션 개발 및 공급
- 주력 제품: 비전 AI 검사기 'GB-Vision', 품질데이터 분석 SaaS
- 2024년 매출: 38억원 / 2023년 매출: 21억원
- 주요 거래처: 대형 식품제조사 4곳, 급식업체 2곳
- 특허: 등록 3건, 출원 5건
- 보유 인증: 없음 (벤처기업확인 미보유, 기업부설연구소 미설립)
- 차입금: 운전자금 12억원 (금리 6.8%, 2026년 9월 만기)
"""

MEETING = """\
미팅 회의록

- 일시: 2026년 5월 20일 14:00~15:30
- 참석자: (주)그린바이트 김도윤 대표, 박서연 경영지원팀장 / venturecompany 이준호 컨설턴트
- 목적: 1차 진단 미팅 (정부지원/세제 컨설팅 가능성 검토)

주요 논의:
1. 대표님은 R&D 인력이 9명인데 기업부설연구소가 없어 세액공제를 못 받고 있는 점을 가장 아쉬워함.
2. 작년 매출이 21억에서 38억으로 급성장했고, 올해 50억 목표. 자금이 빠듯하다고 함.
3. 운전자금 차입금 12억의 금리가 6.8%로 높아 정책자금 대환에 관심.
4. 벤처기업확인을 받은 적이 없음. 받으면 법인세 감면이 가능한지 문의.
5. 내년 신규 공장 설비투자 8억원 예정 — 통합투자세액공제 적용 여부 궁금.
6. 수출은 아직 없으나 일본 식품사와 논의 중.

대표님 Pain Point:
- 세금을 너무 많이 내는 것 같다 (작년 법인세 부담 큼)
- 정부지원사업을 한 번도 받아본 적이 없어 어디서 시작할지 모름
- R&D 인건비 부담이 큼

다음 단계: 재무제표/법인세 신고서 받아 정밀 진단 예정.
"""


def main() -> None:
    notion = NotionAPI(config.NOTION_TOKEN, config.NOTION_VERSION)

    print("회사정보 파일 업로드...")
    comp_id = notion.upload_file("company.txt", COMPANY.encode("utf-8"), "text/plain")
    print("회의록 파일 업로드...")
    meet_id = notion.upload_file("meeting.txt", MEETING.encode("utf-8"), "text/plain")

    body = {
        "parent": {"type": "database_id", "database_id": config.NOTION_DATABASE_ID},
        "properties": {
            "이름": {"title": [{"type": "text", "text": {"content": "(주)그린바이트 1차 미팅"}}]},
            config.PROP_COMPANY: {
                "files": [{"type": "file_upload", "name": "company.txt", "file_upload": {"id": comp_id}}]
            },
            config.PROP_MEETING: {
                "files": [{"type": "file_upload", "name": "meeting.txt", "file_upload": {"id": meet_id}}]
            },
            config.PROP_STATUS: {"select": {"name": config.STATUS_PENDING}},
        },
    }
    page = notion._request("POST", "/pages", json=body)
    print("테스트 row 생성 완료:", page.get("url"))


if __name__ == "__main__":
    main()
