import os
import smtplib
from email.mime.text import MIMEText
import sys
from flask import render_template
from datetime import datetime, timedelta, timezone
import jwt

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from config.settings import Config


def send_verify_email(user_id, user_email):
    """
    # Generate JWT token
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }

    token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
    """
    
    token = user_token(user_id)
    verify_url = Config.VERIFY_URL + f"{token}"
    html_content = render_template(
        "verify_email.html",
        user_email=user_email,
        verify_url=verify_url
    )

    # ✅ Create proper MIME message
    message = MIMEText(html_content, "html")
    message["Subject"] = "Verify Your Email"
    message["From"] = "donot_replay@mixwellsoftware.com"
    message["To"] = user_email

    # ✅ Use SMTP correctly
    with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.EMAIL, Config.APP_PASSWORD)
        server.send_message(message)

    print("Verify Email has been sent to " + Config.EMAIL)
    
def user_token(user_id):
    # Generate JWT token
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
    return token
