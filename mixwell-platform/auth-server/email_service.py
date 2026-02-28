import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import render_template

def send_verify_email(app, email, verify_link):

    with app.app_context():
        html = render_template(
            "email/verify_email.html",
            verify_link=verify_link
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify Your Account"
    msg["From"] = "noreply@mixwellsoftware.com"
    msg["To"] = email

    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login("your_email@gmail.com", "app_password")
    server.sendmail(msg["From"], [email], msg.as_string())
    server.quit()