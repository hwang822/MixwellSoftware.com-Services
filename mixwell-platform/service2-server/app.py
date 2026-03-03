import os, sys, requests

from flask import Flask, render_template, request, redirect
from models import db
import requests

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
AUTH_URL =  Config.AUTH_URL
AUTH_PORT =  Config.AUTH_PORT 
serviceName = "service2"
serviceDesc = "service 2"
serviceUrl = "localhost"
servicePort = "5002"

@app.route("/")
def home():
    token = request.cookies.get("access_token")
    data = {
        "token": token,
        "serviceName": serviceName,
        "serviceDesc": serviceDesc,
        "serviceUrl": serviceUrl,
        "servicePort": servicePort,
    }

    routpath = requests.post(
        f"{AUTH_URL}:{AUTH_PORT}/user/verified",
        json=data   # automatically sets Content-Type: application/json
    )
    
    if routpath.text == "":
        return render_template(f"{serviceName}.html")
    else:
        return redirect(f"{AUTH_URL}:{AUTH_PORT}/user/login?next={serviceUrl}:{servicePort}/")
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=servicePort)
