import os
import sys

from dotenv import load_dotenv
from flask import Flask, make_response, redirect, request, jsonify, render_template, flash, session
from models import db, User, Service, UserService

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

# -------------------------
# SIGNUP
# -------------------------
@app.route("/user/signup", methods=["GET", "POST"])
def user_signup():
    if request.method == "GET":
        return render_template("signup.html")
    session.pop('_flashes', None)
    email = request.form["username"]
    password = generate_password_hash(request.form["password"])    
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
    try:
        decoded = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id = decoded["user_id"]
        user = User.query.filter_by(id=user_id).first()
        if user.is_verified == False:
            user.is_verified = True
            db.session.commit()
        return "Email verified"
    except:
        return "Invalid token"

@app.route("/user/verified", methods=["GET", "POST"])  
def user_verified():
    if request.method == "POST":
        data = request.get_json()
        token = data["token"]        
        serviceName = data["serviceName"]
        serviceDesc = data["serviceDesc"]        
        serviceUrl = data["serviceUrl"]
        servicePort = data["servicePort"]
        if token is None:
            return f"{Config.AUTH_URL}:{Config.AUTH_PORT}/user/login"  # user need login
        decoded = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=["HS256"]
        )
        userid = decoded["user_id"]
        user = User.query.filter_by(id=userid).first()
        if user is None:   
            return f"{Config.AUTH_URL}:{Config.AUTH_PORT}/user/signup"
        else:    
            if user.is_verified == False:
                return f"{Config.AUTH_URL}:{Config.AUTH_PORT}/user/login" # user need watting approve
            else:
                service_register(userid, serviceName, serviceDesc, serviceUrl, servicePort)
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
        response = make_response(
            redirect("http://localhost:5001/")
        )
        r = response.set_cookie(
            "access_token",
            token,
            httponly=True,
            samesite="Lax"
        )
        login_user(user)                
        return response

@app.route("/user/logout")
def logout():
    logout_user()
    return redirect("/uder/login")

def create_admin():
    if User.query.count() == 0:
        admin = User(            
            email="admin",
            password=generate_password_hash("admin123"),
            is_verified = True,
            is_admin = True,
            created_at = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin: admin / admin123")
# -------------------------
# USER DELETE
# -------------------------
@app.route("/user/delete/<int:userid>", methods=["GET", "POST"])
def user_delete(userid):
    user = User.query.get_or_404(userid)
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "user (user_id:{userid} has been deleteed"})

@app.route("/user/approve/<int:userid>")
@login_required
def approve_user(userid):
    if not current_user.is_admin:
        return "Access denied", 403
    user = User.query.get(userid)
    user.is_approved = True
    db.session.commit()
    return

@app.route("/user/remove_service_from_user/<int:user_id>", methods=["POST"])
@login_required
def admin_remove_service_from_user(user_id):  
    results = (
        db.session.query(User, UserService)
        .join(UserService, UserService.userid == user_id)        
        .all()
    )

    service_id = request.form.get("service_id")

    userServices = UserService.query.filter_by(
        userid=user_id,
        serviceid=service_id
    ).all()

    for userService in userServices:        
        db.session.delete(userService)
        db.session.commit()    
    return 


# -------------------------
# SERVICE 
# -------------------------

def service_register(userid, serviceName, serviceDesc, serviceUrl, servicePort):
    # Get or create Service    
    service = Service.query.filter_by(name=serviceName).first()
    if not service:
        service = Service(
                name=serviceName,
                desc = serviceDesc,
                token = "",
                url = serviceUrl,
                port = servicePort,
                starttime = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())                        
            )
        db.session.add(service)
        db.session.flush()   # get service.id without commit

    # Get or create UserService
    userservice = UserService.query.filter_by(
        user_id=userid,
        service_id=service.id
    ).first()

    if not userservice:
        userservice = UserService(
            user_id=userid,
            service_id=service.id,
            access = 1
        )
        db.session.add(userservice)

    db.session.commit()

    return userservice

@app.route("/service/all", methods=["GET", "POST"])
def service_all():
    return Service.query.all()

@app.route("/service/user_with_services")
def user_services():
    return Service.query.all()

@app.route("/service/delete/<int:service_id>", methods=["GET", "POST"])
def service_delete(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()

    return Service.query.all()

@app.route("/service/user_without_services")
def user_without_services():
    return Service.query.all()

@app.route("/service/user_with_services")
def user_with_services():
    return Service.query.all()

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
        create_admin()
    app.run(port=5003)

