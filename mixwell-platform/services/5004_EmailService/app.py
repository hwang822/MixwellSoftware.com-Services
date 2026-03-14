import os, sys
from flask import Flask, redirect, render_template, request
import jwt

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

"""
@app.route("/")
def home():    
    user =  get_user()
    if not user:
        return redirect(authUrl) 
    print(f"Welcome {user['email']} using {user['servicename']}")
    return render_template(f"{serviceName}.html") 

def get_user():     
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user = f"{payload['userid']} + {payload['email']} + {payload['servicename']}"
    except:
        return None        
    return payload
       
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=servicePort)
"""

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

    user =  get_user()
    if not user:
        return redirect(authUrl) 
    print(f"Welcome {user['email']} using {user['servicename']}")


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