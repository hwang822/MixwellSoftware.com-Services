import os
import sys
import json

from dotenv import load_dotenv
from flask import Flask, make_response, redirect, request, jsonify, render_template, flash, session
from models import db, User, Service, UserService, Utility

from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from email_service import send_verify_email, user_token
from sqlalchemy.engine import URL
from sqlalchemy import text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from config.settings import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

#JWT_SECRET = "your_secret_key_here"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/", methods=["GET", "POST"])
def user_auth():
    return redirect("/user/login")

serviceName = "authService"
serviceDesc = "auth Service"
serviceUrl = Config.SERVICE_URL
servicePort = "5003"

service_url = f"{serviceUrl}:{Config.AUTH_PORT}"

# -------------------------
# SIGNUP
# -------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    session.pop('_flashes', None)
    email = request.form["username"]
    password = request.form["password"]        
    Utility.user_signup(email, password)

    user = User(email=email, 
        password=password, 
        is_verified=False, 
        created_at = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())
    )
    try:
        db.session.add(user)
        db.session.commit()
        send_verify_email(user.id, email)
        flash("Signup successful! Waiting for admin approval.")       
        return redirect("/user/login") 
    except:
        db.session.rollback()
        flash("Username already exists.")            
        return redirect("/user/signup")
     
# -------------------------
# VERIFY token   # send link to verify.mixwellsoftware.com with token 
# -------------------------

@app.route("/user/verify/<token>")  
def user_verify(token):
    Utility.user_verify(token)    

@app.route("/user/verified/", methods=["GET"])  
def user_verified():
    data = request.get_json()
    token = data["token"]        
    serviceName = data["serviceName"]
    if token is None:
        return f"{service_url}/user/login"  # user need login
    decoded = jwt.decode(
        token,
        Config.JWT_SECRET,
        algorithms=["HS256"]
    )
    userid = decoded["user_id"]
    user = User.query.filter_by(id=userid).first()
    if user is None:   
        return f"{service_url}/user/signup"
    else:    
        if user.is_verified == False:
            return f"{service_url}/user/login" # user need watting approve
        else:
            Utility.user_add_service(userid, serviceName)
            return ""    
                         
# -------------------------
# LOGIN
# -------------------------
@app.route("/user/login", methods=["GET", "POST"])
def user_login():    
    session.pop('_flashes', None)
    if request.method == "GET":
        return render_template("login.html")        
    session.pop('_flashes', None)
    email = request.form["username"]
    password = request.form["password"]    
    user = User.query.filter_by(email=email).first()

    if user is None:
        flash("Invalid username!.")
        return render_template("login.html")
    elif not check_password_hash(
        user.password, 
        password):
        flash("Invalid password!.")
        return render_template("login.html")
    elif user.is_verified == False:
        flash("Waitting verify email for approve.")
        return render_template("login.html")
    else:
        flash("Login successful!")
        token = user_token(user.id)
        next_url = request.args.get("next")  #next url from send server
        response = make_response(
            redirect(next_url)
        )
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            samesite="Lax"
        )
        login_user(user)                        
        return response
    
# send username and email to auth 
#    data = {"username": Config.ADMIN_NAME,"email": Config.ADMIN_EMAIL}    
#    path = f"{auth_path}/user/add"
#    respose = requests.post(path, json=data)     
#    print(respose.status_code) text["user_id": 1] 200            

@app.route("/user/signup", methods=["POST"]) #
def user_signup():    
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    is_verified = data.get("is_verified")
    is_admin = data.get("is_admin")
    print("email:", email)
    print("password:", password)
    print("is_verified:", is_verified)
    print("is_admin:", is_admin) 
    user = Utility.user_signup(email, password, is_verified, is_admin)
    return {"userId": user.id}, 200   

@app.route("/user/logout")
def logout():
    logout_user()
    return redirect("/uder/login")

# -------------------------
# USER DELETE
# -------------------------
@app.route("/user/remove/<int:userid>", methods=["POST"])
def user_remove(userid):
    return Utility.user_remove(userid)

@app.route("/user/approve/<int:userid>")
@login_required
def user_approve(userid):
    return Utility.user_approve(userid)

@app.route("/user/user_remove_service/<int:user_id>", methods=["POST"])
@login_required
def user_remove_service(user_id):  
    service_id = 0
    return Utility.user_remove_service(user_id, service_id)

# -------------------------
# SERVICE 
# -------------------------

#    Get request and return json as list
#    services = requests.get(f"{auth_path}/service/all").json()    
#    return render_template("portal.html", services=services)
@app.route("/services/get_all", methods=["GET"])
def services_get_all():
    return Utility.services_get_all()

@app.route("/services/add_all", methods=["GET"])
def services_add_all():
    services = request.get_json()  
    Utility.services_add_all(services)
    return ""

@app.route("/service/add", methods=["GET"])
def service_add():
    service = request.get_json()  
    name = service["name"]
    desc = service["desc"]
    url = service["url"]
    port = service["port"]
    return Utility.service_add(name, desc, url, port)

@app.route("/service/remove/<int:service_id>", methods=["GET", "POST"])
def service_remove(service_id):
    return Utility.service_remove(service_id)

@app.route("/service/user_without_services")
def user_without_services():
    userid = 1
    return Utility.user_without_services(userid)

@app.route("/service/user_with_services")
def user_with_services():
    userid = 1
    return Utility.user_with_services(userid)

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=servicePort)

