# Meeting Report Bot

영업 미팅 후 Google Drive에 업로드된 회의록(.txt)과 회사 소개서(.pdf)를
자동으로 분석하여 컨설팅 진단 보고서(.docx)를 생성하는 봇입니다.

## 워크플로우

1. 영업사원이 Drive `inbox/날짜_회사명/` 폴더에 `meeting.txt`와 `company.pdf` 업로드
2. GitHub Actions가 30분마다 폴링
3. Gemini로 보고서 생성 → .docx 변환
4. `done/` 폴더로 결과물 이동

## 기술 스택

- Google Drive API (OAuth 인증)
- Gemini 2.5 Flash (LLM)
- python-docx (보고서 생성)
- GitHub Actions (스케줄링)
