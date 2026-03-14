from flask import Flask, Blueprint, render_template, request
import os
import sys


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import db
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(servicePort)
authUrl = f"{Config.SERVICE_URL}:{Config.PORTAL_PORT}/login?service={serviceName}&next={Config.SERVICE_URL}:{servicePort}"

#BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5004
#os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')

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
    create_app().run(host="127.0.0.1", port=servicePort)