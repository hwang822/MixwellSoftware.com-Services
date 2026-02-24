import os
import sys
from flask import Flask, Blueprint, flash, redirect, render_template, request, session
import requests
BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')

aiService = Blueprint("aiService", __name__)

PORTAL_URL = "http://127.0.0.1:5000"

def sendSignupAPI(username, password):
    response = requests.post(
        f"{PORTAL_URL}/api/signup",
        json={
            "username": username,
            "password": password
        }
    )

    return response

def sendLoginAPI(username, password):
    response = requests.post(
        f"{PORTAL_URL}/api/login",
        json={
            "username": username,
            "password": password
        }
    )
    return response.json()["token"]

def verifyToken(token):
    response = requests.post(
        f"{PORTAL_URL}/api/verify",
        json={"token": token}
    )

    if response.status_code == 200:
        return response.json()["user_id"]

    return None

@aiService.route("/")
def ai_home():
    token = session.get("jwt")

    if not token:
        return redirect("/signup")

    user_id = verifyToken(token)

    if not user_id:
        return redirect("/login")

    return render_template("AIService.html")    

@aiService.route("/login/", methods=["GET","POST"])
def login():  #http://localhost:5001/login
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        token = sendLoginAPI(username, password)
        if not token:
            flash("Invalid login")
            return redirect("/login")
        session["jwt"] = token
        return render_template("aiService.html")
    return render_template("login.html")    

@aiService.route("/signup/", methods=["GET","POST"])
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
    app.register_blueprint(aiService)
    app.config["SECRET_KEY"] = "service-session-secret"
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=BASE_PORT)