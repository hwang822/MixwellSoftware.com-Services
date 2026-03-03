import os, sys, requests
from flask import Blueprint, render_template, request, redirect
from models import db

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
from config.settings import Utility

serviceName = "service1"
serviceDesc = "service 1"
serviceUrl = "localhost"
servicePort = "5001"

service = Blueprint(serviceName, __name__)
@service.route("/", methods=["GET", "POST"])
def home():
    path = f"{serviceName}.html"
    path = "service1.html"
    return render_template("service1.html")
    #token = request.cookies.get("jwt")
    token = request.cookies.get("access_token")
    data = {
        "token": token,
        "serviceName": serviceName,
        "serviceDesc": serviceDesc,
        "serviceUrl": serviceUrl,
        "servicePort": servicePort,
    }
    routpath = requests.post(
        f"http://localhost:5003/user/verified",
        json=data   # automatically sets Content-Type: application/json
    )
    
    if routpath.text == "":
        return render_template(f"{serviceName}.html")
    else:
        return redirect(routpath.text)
        
Utility.create_app(service, servicePort, db)

