from flask import Flask, Blueprint, render_template, request, jsonify
import sys, imaplib, email, smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
sys.path.insert(0, f"{app.root_path}/../../")
from config.settings import Config
from models import Utility

serviceport = int(app.root_path.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

# =========================
# IMAP: READ EMAILS
# =========================
def check_emails():
    mail = imaplib.IMAP4_SSL("imap.zoho.com")
    mail.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
    mail.select("INBOX")

    status, messages = mail.search(None, "ALL")
    mail_ids = messages[0].split()

    email_list = []

    for mail_id in mail_ids[::-1][:20]:
        status, msg_data = mail.fetch(mail_id, "(RFC822)")

        for part in msg_data:
            if isinstance(part, tuple):
                msg = email.message_from_bytes(part[1])

                body = ""
                if msg.is_multipart():
                    for p in msg.walk():
                        if p.get_content_type() == "text/plain":
                            body = p.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                email_list.append({
                    "id": mail_id.decode(),
                    "from": msg.get("from"),
                    "subject": msg.get("subject"),
                    "date": msg.get("date"),
                    "body": body
                })

    mail.logout()
    return email_list


# =========================
# SMTP: SEND EMAIL
# =========================
def send_email(to, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_EMAIL
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.zoho.com", 465) as server:
        server.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
        server.send_message(msg)

def delete_email(mail_id):
    import imaplib

    mail = imaplib.IMAP4_SSL("imap.zoho.com")
    mail.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)

    mail.select("INBOX")

    # Mark email as deleted
    mail.store(mail_id, '+FLAGS', '\\Deleted')

    # Permanently remove
    mail.expunge()

    mail.logout()

# =========================
# ROUTES
# =========================
emailService = Blueprint("emailService", __name__)
@emailService.route("/")
def inbox():
    return render_template("email.html")


@emailService.route("/api/emails")
def get_emails():
    return jsonify(check_emails())


@emailService.route("/api/send", methods=["POST"])
def send_email_api():
    data = request.json
    send_email(data["to"], data["subject"], data["body"])
    return jsonify({"status": "ok"})


@emailService.route("/api/delete", methods=["POST"])
def delete_email_api():
    data = request.json
    mail_id = data.get("id")

    delete_email(mail_id)

    return jsonify({"status": "deleted"})

def create_app():
    app.register_blueprint(emailService)
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)
