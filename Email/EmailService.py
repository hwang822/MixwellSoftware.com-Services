from flask import Flask, request, render_template_string
import smtplib
from email.mime.text import MIMEText
import datetime

app = Flask(__name__)

# ===== Zoho 邮件配置 =====
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 465
EMAIL_USER = "henrywang@mixwellsoftware.com"
EMAIL_PASS = "Delanyin@00"

# ===== 发邮件函数 =====
def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# ===== 首页 + 联系表单 =====
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        msg = request.form.get("message")

        body = f"""
New Contact Message

Name: {name}
Email: {email}
Message:
{msg}

Time: {datetime.datetime.now()}
IP: {request.remote_addr}
"""

        send_email("New Website Contact", body)

        return "<h2>Message Sent ✅</h2>"

    return """
    <h1>Mixwell Software</h1>
    <h2>Contact Us</h2>

    <form method="post">
        Name:<br>
        <input name="name"><br><br>

        Email:<br>
        <input name="email"><br><br>

        Message:<br>
        <textarea name="message"></textarea><br><br>

        <button type="submit">Send</button>
    </form>

    <br><br>
    <a href="/videos">Go To Videos</a>
    """

# ===== 视频页 + Alert 邮件 =====
@app.route("/videos")
def videos():

    body = f"""
Video Page Access Alert

Time: {datetime.datetime.now()}
IP: {request.remote_addr}
User-Agent: {request.headers.get('User-Agent')}
"""

    send_email("Video Site Access Alert", body)

    return """
    <h1>Travel Videos</h1>

    <video width="720" controls>
        <source src="/static/video.mp4" type="video/mp4">
    </video>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8040)