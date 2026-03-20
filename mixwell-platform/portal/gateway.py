import sys
from flask_login import LoginManager, logout_user
from flask import Flask, flash, make_response, redirect, render_template, request, session
from flask import Flask, render_template, send_file
import qrcode
import os

app = Flask(__name__)

BASE_DIR = f"{app.root_path}/../"  
sys.path.insert(0, BASE_DIR)

from config.settings import Config
from models import Utility, db, Utility, User

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


serviceport = 5500
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 
print (f"Portal Service port# {serviceport}")

servicedb = "auth"  #sys.argv[2]
dbport = 5000

serviceName = "gateway"

authUrl = f"http://{Config.SERVICE_URL}:{serviceport}/login?next=http://{Config.SERVICE_URL}:{serviceport}"

dbname = "auth_5000"
if serviceport >= 8000:
    dbname = "auth_8000"
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/{dbname}"

app.config["SQLALCHEMY_DATABASE_URI"] = auth_db 
db.init_app(app)    


SERVICES_PATH = f"{BASE_DIR}\\services"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/service/<servicename>")
def serivce_access(servicename):
    user = Utility.user_check(servicename)    
    if not user:
        return redirect(authUrl)    
    service = Utility.service_get(servicename)    
    if service:
        return redirect(f"{service.url}/user/{user.id}")
    
@app.route("/")
def home():
    services = Utility.services_get_all()
    user = Utility.user_check(serviceName)
    if not user:
        return render_template("portal.html", services = services)    
    return redirect(f"http://localhost:5007/user/{user.id}") #, username = user.email, user_with_services = user_with_services)

# -------------------------
# user signup, login, logout request from auth UI 
# -------------------------
@app.route("/signup", methods=["GET", "POST"])  
def signup():    
    if request.method == "GET":      
        #session.pop('_flashes', None)  
        return render_template("signup.html")
    email = request.form["username"]
    password = request.form["password"]        
    response = Utility.user_signup(email, password, False, False)
    #flash(response["message"])
    if response["status"] == 400:  
        return redirect("/signup")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():          
    if request.method == "GET":
        #session.pop('_flashes', None)        
        return render_template("login.html")                
    email = request.form["username"]
    password = request.form["password"]    
    response = Utility.user_login(email, password)    
    #flash(response["message"])
    if response["status"] == 400:
        return redirect("/login")
    else :  
        #flash(response["message"])
        currentuser = response["data"]
        next_url = request.args.get("next")
        servicename = request.args.get("service")
        token = Utility.user_token(currentuser.id, currentuser.email, servicename)                    
        if next_url is None:  
            response = make_response(redirect("/"))  # back to portal 
        else:
            response = make_response(redirect(next_url)) # back to service
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            samesite="Lax"
        ) 
        return response       

@app.route("/logout", methods=["GET", "POST"])
def logout():    
    logout_user()
    return render_template(f"{serviceName}.html")

@app.route("/services/service_download/<servicename>")
def service_download(servicename):     
    return render_template("servicedownload.html")


# -----------------------------
# Download page
# -----------------------------
@app.route("/download")
def download_page():
    return render_template("download.html")


# -----------------------------
# Windows EXE
# -----------------------------
@app.route("/download/win")
def download_win():
    return send_file(
        "static/downloads/Mixwell.exe",
        as_attachment=True
    )


# -----------------------------
# Android APK
# -----------------------------
@app.route("/download/apk")
def download_apk():
    return send_file(
        "static/downloads/mixwell.apk",
        as_attachment=True
    )


# -----------------------------
# QR Generator
# -----------------------------
@app.route("/qrcode/<platform>")
def generate_qr(platform):
    if platform == "ios":
        url = BASE_URL   # iOS 用 Web/PWA
    elif platform == "android":
        url = BASE_URL + "/download/apk"
    else:
        url = BASE_URL

    img = qrcode.make(url)
    path = f"static/qrcode_{platform}.png"
    img.save(path)

    return send_file(path, mimetype="image/png")

if __name__ == "__main__":
    with app.app_context():    
        db.create_all()        
    app.run(port=serviceport, debug=False, use_reloader=False)

# GatewayRoute.py