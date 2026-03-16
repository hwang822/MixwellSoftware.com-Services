from flask import Flask, Blueprint, render_template, request
import os
import sys


#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
#sys.path.insert(0, BASE_DIR)
app = Flask(__name__)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(sys.argv[1]) if len(sys.argv) > 1 else int(servicePort)

emailService = Blueprint("emailService", __name__)

def send_email():
    return "Email Sent!"

@emailService.route("/")
def Email_home():
    return render_template(f"{serviceName}.html")

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
    create_app().run(host="127.0.0.1", port=servicePort)