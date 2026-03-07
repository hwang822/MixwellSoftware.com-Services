import os
import sys
import jwt
from flask import Flask, make_response, redirect, render_template, request
import requests

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from config.settings import Config

app = Flask(__name__)
app.config.from_object(Config)

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
currentuser = []

# ---------- Login, siginup, logout ROUTES ----------

@app.route("/")
def home():

    # 1️⃣ token returned from auth
    token = request.args.get("token")
    if token:
        response = make_response(redirect("/"))
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            samesite="Lax"
        )
        return response

    # 2️⃣ check existing cookie
    token = request.cookies.get("access_token")
    if not token:
        return redirect(f"{auth_path}/login?next={serviceUrl}:{servicePort}/")        
    try:
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return redirect(f"{auth_path}/login?next={serviceUrl}:{servicePort}/")        

    currentuserid = decoded["user_id"]
    user = requests.get(f"{auth_path}/user/user_get/{currentuserid}").json()
    is_adimin = user["is_admin"]        
    userswithoutservices = requests.get(f"{auth_path}/user/user_without_services/{currentuserid}").json()            
    userswithservices = requests.get(f"{auth_path}/user/user_with_services/{currentuserid}").json()                    
    if is_adimin:
        users = requests.get(f"{auth_path}/users/get_all").json()
        services = requests.get(f"{auth_path}/services/get_all").json()    
        return render_template("admin_dashboard.html", 
            users = users,
            services = services, 
            userswithservices = userswithservices, 
            userswithoutservices = userswithoutservices)
    else:
        return render_template("admin_dashboard.html", userswithservices = userswithservices)     

@app.route("/users/user_add/<int:userid>")
def user_add(userid):
    return userid
@app.route("/users/user_remove/<int:userid>")
def user_remove(userid):
    return userid
@app.route("/users/user_add_service/<int:userid>")
def user_add_service(userid):
    return userid
@app.route("/users/user_remove_service/<int:userid>")
def user_remove_service(userid):
    return userid
@app.route("/services/service_remove/<int:serviceid>")
def service_remove(serviceid):
    return serviceid
@app.route("/services/service_start/<int:serviceid>")
def service_start(serviceid):
    return serviceid

def home_insital():
    services = [
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
    path = f"{auth_path}/services/add_all"
    respose = requests.get(path, json=services) 

    # add admin user first. 
    user = {"email": Config.ADMIN_NAME,"password": Config.ADMIN_PASSWORD, "is_verified": True, "is_admin":True}    
    path = f"{auth_path}/user/user_signup"
    respose = requests.get(path, json=user)  
    #print(respose.status_code)

    #add service infomation to db
    service = {"name": serviceName,"desc": serviceDesc,"url": serviceUrl,"port": servicePort}    
    path = f"{auth_path}/service/add"
    respose = requests.get(path, json=service)        

if __name__ == "__main__":
#    with app.app_context():
#        db.create_all()
#        create_admin()
    home_insital()

    app.run(port=servicePort)
    #socketio.run(app, debug=False, port=BASE_PORT)
