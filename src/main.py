import os, sys, tempfile, traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from drive_client import DriveClient
from file_parser import read_txt, extract_pdf_text
from gemini_client import generate_report
from docx_builder import build_docx
from mailer import send_completion_email
from notion_client import create_meeting_subpage

INBOX_ID            = os.environ['INBOX_FOLDER_ID']
PROCESSING_ID       = os.environ['PROCESSING_FOLDER_ID']
DONE_ID             = os.environ['DONE_FOLDER_ID']
ERROR_ID            = os.environ['ERROR_FOLDER_ID']
NOTION_PARENT_ID    = os.environ.get('NOTION_PARENT_PAGE_ID', '')

def main():
    drive = DriveClient()
    folders = drive.list_subfolders(INBOX_ID)

    if not folders:
        print("📭 처리할 미팅 폴더 없음")
        return

    for folder in folders:
        name = folder['name']
        fid  = folder['id']

        files = drive.list_files_in_folder(fid)
        file_map = {f['name']: f for f in files}

        if 'meeting.txt' not in file_map or 'company.pdf' not in file_map:
            print(f"⏭ 스킵 ({name}): meeting.txt 또는 company.pdf 없음")
            continue

        print(f"▶ 처리 시작: {name}")
        drive.move_folder(fid, PROCESSING_ID)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                txt_path  = os.path.join(tmpdir, 'meeting.txt')
                pdf_path  = os.path.join(tmpdir, 'company.pdf')
                docx_path = os.path.join(tmpdir, 'meeting-report.docx')

                print(f"  📥 파일 다운로드 중...")
                drive.download_file(file_map['meeting.txt']['id'], txt_path)
                drive.download_file(file_map['company.pdf']['id'], pdf_path)

                print(f"  📄 파일 파싱 중...")
                meeting_text = read_txt(txt_path)
                company_text = extract_pdf_text(pdf_path)

                print(f"  🤖 Gemini 보고서 생성 중...")
                report_data = generate_report(meeting_text, company_text)

                print(f"  📝 .docx 생성 중...")
                build_docx(report_data, docx_path)

                print(f"  📤 Drive 업로드 중...")
                upload_result = drive.upload_file(docx_path, fid, 'meeting-report.docx')
                docx_file_id = upload_result.get('id', '')

            drive.move_folder(fid, DONE_ID)
            drive_link = f"https://drive.google.com/drive/folders/{DONE_ID}"
            meeting_folder_url = f"https://drive.google.com/drive/folders/{fid}"

            notion_link = ""
            if NOTION_PARENT_ID:
                try:
                    print(f"  📝 Notion 페이지 생성 중...")
                    docx_external_url = ""
                    if docx_file_id:
                        drive.share_anyone_with_link(docx_file_id)
                        docx_external_url = f"https://drive.google.com/uc?export=download&id={docx_file_id}"
                    notion_link = create_meeting_subpage(
                        parent_page_id=NOTION_PARENT_ID,
                        meeting_name=name,
                        drive_folder_url=meeting_folder_url,
                        docx_external_url=docx_external_url,
                        docx_filename='meeting-report.docx',
                        report_data=report_data,
                    )
                except Exception as ne:
                    print(f"⚠️ Notion 업데이트 실패 ({name}): {type(ne).__name__}: {ne}")

            send_completion_email(name, 'meeting-report.docx', drive_link, notion_link)
            print(f"✅ 완료: {name}")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ 오류 ({name}): {error_msg}")
            drive.upload_text_file(error_msg, fid, 'error.log')
            drive.move_folder(fid, ERROR_ID)

if __name__ == '__main__':
    main()
