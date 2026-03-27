from flask import Flask, Blueprint, jsonify, render_template, request
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

@emailService.route("/check_email", methods=["GET"])
def receive_email_api():
    request = Utility.check_inbox()
    data = request.json    
    return jsonify({"status": "sent"})

@emailService.route("/email/", methods=["GET", "POST"])
def sendEmail():
    if request.method == "POST":
        emailfrom = request.form.get("emailto") #"support@mixwellsoftware.com"
        emailto = request.form.get("emailto")
        msg = request.form.get("message")
        subject = request.form.get("subject")       
        Utility.send_email(emailto, emailfrom, subject, msg)

def create_app():
    app.register_blueprint(emailService)
    receive_email_api()
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)