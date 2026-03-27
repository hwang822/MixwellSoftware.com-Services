from flask import Flask, Blueprint, jsonify, render_template, request
import sys

app = Flask(__name__)
apppath = app.root_path
projectpath = f"{apppath}/../../"  
sys.path.insert(0, projectpath)

from config.settings import Config
from models import Utility

result = apppath.rsplit("_")
serviceport = int(result[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

#serviceport = int(sys.argv[1])
#servicedb = sys.argv[2]
#app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 

emailService = Blueprint("emailService", __name__)

def send_email():
    return "Email Sent!"

#from flask import Flask, request, jsonify

#app = Flask(__name__)

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
    #app = Flask(__name__)
    app.register_blueprint(emailService)
    receive_email_api()
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)