import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

def send_email(config: Dict, subject: str, content: str):
    """发送邮件通知"""
    msg = MIMEMultipart()
    msg['From'] = config['sender']
    msg['To'] = ', '.join(config['receivers'])
    msg['Subject'] = subject
    
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['sender'], config['password'])
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise Exception(f"发送邮件失败: {str(e)}") 