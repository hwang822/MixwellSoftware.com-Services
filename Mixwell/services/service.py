import datetime
import sys
from flask import Flask, Blueprint, flash, redirect, render_template, request, session
import requests
from datetime import datetime  

SERVICENAME = "service"
SERVICEDESC = "service"
SERVICEPATH = SERVICENAME + "\\templates\\" + SERVICENAME + ".html" 
URL = "127.0.0.1"
BASE_PORT = 5000

BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else BASE_PORT
SERVICE_PORT = BASE_PORT+1
service = Blueprint(SERVICENAME, __name__)

PORTAL_URL = f"http://{URL}:{BASE_PORT}"

def sendServiceSignupAPI(servicename, servicedesc, url, port):
    payload ={
        "servicename": servicename,
        "servicedesc": servicedesc,
        "url": url,
        "port": port
    }
    response = requests.post(
        f"{PORTAL_URL}/api/serviceregister",
        json=payload
        )              
    return response

def sendSignupAPI(username, password):
    response = requests.post(
        f"{PORTAL_URL}/api/usersignup",
        json={
            "username": username,
            "password": password
        }
    )

    return response

def sendLoginAPI(username, password, servicename):
    response = requests.post(
        f"{PORTAL_URL}/api/userlogin",
        json={
            "username": username,
            "password": password,
            "servicename": servicename
        }
    )
    return response.json()["token"]

def verifyToken(token):
    response = requests.post(
        f"{PORTAL_URL}/api/userverify",
        json={"token": token}
    )

    if response.status_code == 200:
        return response.json()["user_id"]
    return None

@service.route("/")
def ai_home():
    token = session.get("jwt")    
    if not token:
        return redirect("/signup")
    response = verifyToken(token)
    if response is None:
        return redirect("/login")
    return render_template("service.html")    

@service.route("/login/", methods=["GET","POST"])
def login():  #http://localhost:5001/login 
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        token = sendLoginAPI(username, password, SERVICENAME)
        if not token:
            flash("Invalid login")
            return redirect("/login")
        session["jwt"] = token
        return render_template("service.html")            
    return render_template("login.html")    

@service.route("/signup/", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"] 
        response = sendSignupAPI(username, password)
        if response.status_code == 200:
            return redirect("/login")
    return render_template("signup.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(service)
    app.config["SECRET_KEY"] = "service-session-secret"
    sendServiceSignupAPI(SERVICENAME, SERVICEDESC, URL, SERVICE_PORT)
    return app

if __name__ == "__main__":
    create_app().run(host=URL, port=SERVICE_PORT)
