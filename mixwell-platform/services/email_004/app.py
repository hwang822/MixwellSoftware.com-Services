from flask import Flask, Blueprint, render_template, request
import os
import sys


app = Flask(__name__)
sys.path.insert(0, f"{app.root_path}/../../")
from models import Utility

serviceport = int(app.root_path.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

emailService = Blueprint("emailService", __name__)
@emailService.route("/")
def Email_home():
    return render_template("email.html")

@emailService.route("/send_email/", methods=["GET", "POST"])
def sendEmail():
    if request.method == "POST":
        emailto = request.form.get("emailto")
        emailfrom = request.form.get("emailfrom")
        subject = request.form.get("subject")
        message = request.form.get("message")        
        return Utility.send_email(emailto, emailfrom, subject, message)
    return render_template("EmailService.html")

@emailService.route("/checkemail/", methods=["GET", "POST"])
def checkemail():
    emails = Utility.check_emails(10)
    return render_template("EmailService.html", emails)

def create_app():
    app.register_blueprint(emailService)
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)