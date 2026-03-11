import os
import sys
from flask_login import LoginManager, login_user, logout_user
import jwt
from flask import Flask, flash, make_response, redirect, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import Utility, db, Utility, User, UserService
import requests

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#if BASE_DIR not in sys.path:
#    sys.path.insert(0, BASE_DIR)
#from settings import Config
#from auth.models import db, Utility, User, UserService
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
from config.settings import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#api = Blueprint("api", __name__)

# Flask session secret
app.config["SECRET_KEY"] = "service-session-secret"

serviceName = "portalService"
serviceDesc = "Portal Service"
serviceUrl =  Config.SERVICE_URL
servicePort = Config.PORTAL_PORT

auth_path = f"{serviceUrl}:{Config.AUTH_PORT}"
service_path = f"{serviceUrl}:{servicePort}"
services = []
users = []
userswithservices = []
userswithoutservices = []
currentuser = None

# ---------- Login, siginup, logout ROUTES ----------

@app.route("/")
def home():
    token = request.cookies.get("access_token")
    services = Utility.services_get_all()
    if not token:
        return redirect("/logout")

    try:
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        userid = decoded["user_id"]
        user = Utility.user_get(userid)

        if user.is_admin:
            users = Utility.users_get_all()
                
            return render_template("admin_dashboard.html", services = services, users = users)     
        else:
            userswithservices = Utility.user_with_services(user.id)
            return render_template("user_dashboard.html", userswithservices = userswithservices)                     
    except:
        return redirect("/logout")

# -------------------------
# user signup, login, logout request from auth UI 
# -------------------------
@app.route("/signup", methods=["GET", "POST"])  
def signup():    
    if request.method == "GET":        
        return render_template("signup.html")
    session.pop('_flashes', None)
    email = request.form["username"]
    password = request.form["password"]        
    response = Utility.user_signup(email, password, False, False)
    flash(response["message"])
    if response["status"] == 400:  
        return redirect("/signup")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():          
    if request.method == "GET":
        return render_template("login.html")        
    session.pop('_flashes', None)    
    email = request.form["username"]
    password = request.form["password"]    
    response = Utility.user_login(email, password)    
    flash(response["message"])
    if response["status"] == 400:
        return redirect("/login")
    else :  
        flash(response["message"])
        user = response["data"]
        token = Utility.user_token(user.id)            
        next_url = request.args.get("/")  
        response = make_response(redirect(next_url))
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            samesite="Lax"
        ) 
        return response       
        #return redirect("/")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop('_flashes', None)
    logout_user()
    return redirect("/login")

@app.route("/users/user_remove/<int:userid>") 
def user_remove(userid):
    return Utility.user_remove(userid)

@app.route("/users/user_approve/<int:userid>")   #GOOD
def user_approve(userid):
    return Utility.user_approve(userid)
                    
@app.route("/users/user_add_service/<int:userid>")
def user_add_service(userid, serviceid):
    return Utility.user_add_service(userid, serviceid)

@app.route("/users/user_remove_service/<int:userid>")
def user_remove_service(userid, serviceid):
    return Utility.user_remove_service(userid, serviceid)

@app.route("/services/service_add")
def service_add():
    name = request.form["name"]
    desc = request.form["desc"]    
    url = request.form["url"]
    port = request.form["port"]    
    return Utility.service_add(name, desc, url, port)

@app.route("/services/service_remove/<int:serviceid>")
def service_remove(serviceid):
    return Utility.service_remove(serviceid)
    
@app.route("/services/service_start/<int:serviceid>")
def service_start(serviceid):
    return Utility.service_start(serviceid)

def home_insital():
    servicesList = [
        {"name": "PortalService", "desc": "Portal Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)}"},
        {"name": "AuthService", "desc": "Auth Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+1}"},
        {"name": "AIService", "desc": "AI Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+2}"},
        {"name": "CamService", "desc": "Cam Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+3}"},
        {"name": "VideoService", "desc": "Video Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+4}"},
        {"name": "EmailService", "desc": "Email Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+5}"},
        {"name": "TravelService", "desc": "Travel Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+6}"},
        {"name": "DataAPIService", "desc": "Data Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+7}"},
        {"name": "RdpService", "desc": "RDP Service", "url": f"{Config.GATWAY_URL}", "port": f"{int(Config.PORTAL_PORT)+8}"}
    ]        
    services = Utility.services_add_all(servicesList)
    Utility.service_add(serviceName, serviceDesc, serviceUrl, servicePort)    
    Utility.user_signup(Config.ADMIN_NAME, Config.ADMIN_PASSWORD, True, True)
    
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
        home_insital()    
    app.run(port=servicePort)
