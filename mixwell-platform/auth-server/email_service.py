import smtplib
from email.mime.text import MIMEText
from flask import render_template
from datetime import datetime, timedelta, timezone
import jwt
from config import Config

def send_verify_email(user_id, user_email):

    # Generate JWT token
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }

    token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
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
    
