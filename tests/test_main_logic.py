import os
import sys
from unittest import TestCase, mock

# Set dummy environment variables so main.py imports successfully
os.environ['INBOX_FOLDER_ID'] = 'dummy_inbox'
os.environ['PROCESSING_FOLDER_ID'] = 'dummy_processing'
os.environ['DONE_FOLDER_ID'] = 'dummy_done'
os.environ['ERROR_FOLDER_ID'] = 'dummy_error'

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.main import main

class TestMeetingReportBot(TestCase):
    @mock.patch('src.main.DriveClient')
    @mock.patch('src.main.read_txt')
    @mock.patch('src.main.extract_pdf_text')
    @mock.patch('src.main.generate_report')
    @mock.patch('src.main.build_docx')
    @mock.patch('src.main.send_completion_email')
    @mock.patch('src.main.create_meeting_subpage')
    def test_meeting_txt_processing(self, mock_create_page, mock_send_email, mock_build_docx,
                                    mock_generate_report, mock_extract_pdf, mock_read_txt, mock_drive_client_class):
        # Setup mocks
        mock_drive = mock.MagicMock()
        mock_drive_client_class.return_value = mock_drive
        
        # Mock subfolders in inbox
        mock_drive.list_subfolders.return_value = [{'id': 'folder123', 'name': '20260527_VentureCompany'}]
        
        # Mock files in subfolder (with meeting.txt and company.pdf)
        mock_drive.list_files_in_folder.return_value = [
            {'id': 'meeting_txt_id', 'name': 'meeting.txt'},
            {'id': 'company_pdf_id', 'name': 'company.pdf'}
        ]
        
        # Mock download / upload
        mock_drive.upload_file.return_value = {'id': 'docx_file_id'}
        
        # Mock parsing
        mock_read_txt.return_value = "This is meeting txt contents"
        mock_extract_pdf.return_value = "This is company pdf contents"
        
        # Mock report generation
        mock_generate_report.return_value = {"dummy": "data"}
        
        # Run main
        main()
        
        # Asserts
        # Ensure meeting.txt was read using read_txt
        mock_read_txt.assert_called_once()
        # Ensure company.pdf was read using extract_pdf_text
        mock_extract_pdf.assert_called_once_with(mock.ANY)
        # Ensure download was called for meeting.txt and company.pdf
        self.assertEqual(mock_drive.download_file.call_count, 2)
        
    @mock.patch('src.main.DriveClient')
    @mock.patch('src.main.read_txt')
    @mock.patch('src.main.extract_pdf_text')
    @mock.patch('src.main.generate_report')
    @mock.patch('src.main.build_docx')
    @mock.patch('src.main.send_completion_email')
    @mock.patch('src.main.create_meeting_subpage')
    def test_meeting_pdf_processing(self, mock_create_page, mock_send_email, mock_build_docx,
                                    mock_generate_report, mock_extract_pdf, mock_read_txt, mock_drive_client_class):
        # Setup mocks
        mock_drive = mock.MagicMock()
        mock_drive_client_class.return_value = mock_drive
        
        # Mock subfolders in inbox
        mock_drive.list_subfolders.return_value = [{'id': 'folder123', 'name': '20260527_VentureCompany'}]
        
        # Mock files in subfolder (with meeting.pdf and company.pdf)
        mock_drive.list_files_in_folder.return_value = [
            {'id': 'meeting_pdf_id', 'name': 'meeting.pdf'},
            {'id': 'company_pdf_id', 'name': 'company.pdf'}
        ]
        
        # Mock download / upload
        mock_drive.upload_file.return_value = {'id': 'docx_file_id'}
        
        # Mock parsing
        # First call is for meeting.pdf, second for company.pdf
        mock_extract_pdf.side_effect = ["This is meeting pdf contents", "This is company pdf contents"]
        
        # Mock report generation
        mock_generate_report.return_value = {"dummy": "data"}
        
        # Run main
        main()
        
        # Asserts
        # Ensure read_txt was NEVER called because we had a PDF meeting log
        mock_read_txt.assert_not_called()
        # Ensure extract_pdf_text was called twice (once for meeting.pdf, once for company.pdf)
        self.assertEqual(mock_extract_pdf.call_count, 2)
        # Ensure download was called for meeting.pdf and company.pdf
        self.assertEqual(mock_drive.download_file.call_count, 2)
