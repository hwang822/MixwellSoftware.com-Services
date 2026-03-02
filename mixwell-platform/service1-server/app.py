import os
import sys

from flask import Flask, render_template, request, redirect
from models import db
from flask import request, redirect, render_template
import jwt
import requests


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from config.settings import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

serviceName = "service1"
serviceDesc = "service 1"
serviceUrl = "localhost"
servicePort = "5001"

@app.route("/")
def home():

    token = request.cookies.get("access_token")
    if not token:
        authPath = Config.AUTH_URL + ":" + Config.AUTH_PORT + "/user/signup"
        return redirect(authPath)

    decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    user_id = decoded["user_id"]    
    payload ={
        "servicename": serviceName,
        "servicedesc": serviceDesc,
        "url": serviceUrl,
        "port": servicePort,
        "userid" : user_id
    }

    authPath = Config.AUTH_URL + ":" + Config.AUTH_PORT + "/user/verified"
    response = requests.post(
        authPath,
        json=payload
        )        
    if response.status_code == 200:
        return render_template(f"{serviceName}.html")        
    else:
        authPath = Config.AUTH_URL + ":" + Config.AUTH_PORT + "/user/login"
        return redirect(authPath)
    
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=5001)