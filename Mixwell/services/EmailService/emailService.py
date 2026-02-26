from flask import Flask, Blueprint, render_template, request
from flask import Flask, Blueprint, render_template
import os
import sys
from flask import Flask, Blueprint
BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5004
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')

emailService = Blueprint("emailService", __name__)

def send_email():
    return "Email Sent!"

@emailService.route("/")
def Email_home():
    return render_template("EmailService.html")

@emailService.route("/email/", methods=["GET", "POST"])
def sendEmail():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        msg = request.form.get("message")        
        return send_email()

    return render_template("EmailService.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(emailService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=BASE_PORT)