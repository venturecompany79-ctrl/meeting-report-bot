import json, os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'token.json')

class DriveClient:
    def __init__(self):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
        self.service = build('drive', 'v3', credentials=creds)

    def list_subfolders(self, parent_id):
        query = f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def list_files_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        return results.get('files', [])

    def download_file(self, file_id, save_path):
        request = self.service.files().get_media(fileId=file_id)
        with open(save_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    def upload_file(self, local_path, folder_id, filename):
        metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaFileUpload(local_path, resumable=False)
        return self.service.files().create(
            body=metadata,
            media_body=media,
            fields='id'
        ).execute()

    def move_folder(self, folder_id, new_parent_id):
        file = self.service.files().get(fileId=folder_id, fields='parents').execute()
        prev_parents = ",".join(file.get('parents', []))
        self.service.files().update(
            fileId=folder_id,
            addParents=new_parent_id,
            removeParents=prev_parents,
            fields='id, parents'
        ).execute()

    def upload_text_file(self, content, folder_id, filename):
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        self.upload_file(tmp_path, folder_id, filename)
        os.unlink(tmp_path)

    def share_anyone_with_link(self, file_id):
        self.service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'},
            fields='id'
        ).execute()
