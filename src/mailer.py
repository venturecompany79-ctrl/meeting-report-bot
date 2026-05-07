import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime

def send_completion_email(company_name: str, report_filename: str, drive_link: str):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Meeting Report Bot] 보고서 생성 완료 — {company_name}"
    msg["From"] = gmail_user
    msg["To"] = gmail_user

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #051C2A; max-width: 600px; margin: auto; padding: 32px;">
      <div style="border-left: 4px solid #163E93; padding-left: 16px; margin-bottom: 24px;">
        <p style="color: #30A3DA; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 1px;">Meeting Report Bot</p>
        <h2 style="color: #163E93; margin: 4px 0;">보고서 생성 완료</h2>
      </div>
      <table style="border-collapse: collapse; width: 100%; margin-bottom: 24px;">
        <tr style="background: #f4f7fb;">
          <td style="padding: 10px 16px; font-weight: bold; width: 120px;">회사명</td>
          <td style="padding: 10px 16px;">{company_name}</td>
        </tr>
        <tr>
          <td style="padding: 10px 16px; font-weight: bold;">파일명</td>
          <td style="padding: 10px 16px;">{report_filename}</td>
        </tr>
        <tr style="background: #f4f7fb;">
          <td style="padding: 10px 16px; font-weight: bold;">생성 시각</td>
          <td style="padding: 10px 16px;">{now}</td>
        </tr>
      </table>
      <a href="{drive_link}" style="background: #163E93; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin-bottom: 32px;">
        📂 Drive에서 보고서 열기
      </a>
      <p style="color: #aaa; font-size: 11px; border-top: 1px solid #eee; padding-top: 16px;">© 2026 venturecompany. Meeting Report Bot</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, gmail_user, msg.as_string())

    print(f"✅ 메일 발송 완료: {company_name}")
