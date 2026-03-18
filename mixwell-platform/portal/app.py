import os
import sys
from flask_login import LoginManager, logout_user
from flask import Flask, flash, make_response, redirect, render_template, request, session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, BASE_DIR)

from config.settings import Config
from models import Utility, db, Utility, User

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

SERVICES_PATH = f"{BASE_DIR}\\services"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#folder_name = os.path.basename(os.path.dirname(__file__))
#servicePort, serviceName = folder_name.split("_", 1)

serviceName = "portal"
servicePort = Config.PORTAL_PORT
servicePort = int(sys.argv[1]) if len(sys.argv) > 1 else int(servicePort) 

authUrl = f"http://{Config.SERVICE_URL}:{servicePort}/login?next=http://{Config.SERVICE_URL}:{servicePort}"

# ---------- Login, siginup, logout ROUTES ----------

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
        return render_template(f"{serviceName}.html", services = services)    
    try:
        if user.is_admin:
            users = Utility.users_list()
            return render_template("admin_dashboard.html", services = services, users = users)     
        else:
            return redirect(f"http://localhost:5007/user/{user.id}") #, username = user.email, user_with_services = user_with_services)
    except:
        return render_template("admin_dashboard.html", services = services)    

# -------------------------
# user signup, login, logout request from auth UI 
# -------------------------
@app.route("/signup", methods=["GET", "POST"])  
def signup():    
    if request.method == "GET":      
        session.pop('_flashes', None)  
        return render_template("signup.html")
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
        session.pop('_flashes', None)        
        return render_template("login.html")                
    email = request.form["username"]
    password = request.form["password"]    
    response = Utility.user_login(email, password)    
    flash(response["message"])
    if response["status"] == 400:
        return redirect("/login")
    else :  
        flash(response["message"])
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

@app.route("/users/user_remove/<int:userid>") 
def user_remove(userid):
    Utility.user_remove(userid)
    return redirect("/")

@app.route("/users/user_approve/<int:userid>")
def user_approve(userid):
    Utility.user_approve(userid)
    return redirect("/")

@app.route("/users/user_verify/<token>")
def user_verify(token):
    Utility.user_verify(token)
    return redirect("/")

@app.route("/users/user_add_service", methods=["POST"])
def user_add_service():
    userid = request.form.get("userid")
    serviceid = request.form.get("serviceid")
    Utility.user_add_service(userid, serviceid)
    return redirect("/")    

@app.route("/users/user_remove_service", methods=["POST"])
def user_remove_service():
    userid = int(request.form.get("userid"))
    serviceid = int(request.form.get("serviceid"))
    Utility.user_remove_service(userid, serviceid)
    return redirect("/")    

@app.route("/services/service_remove/<int:serviceid>")
def service_remove(serviceid):
    Utility.service_remove(serviceid)
    return redirect("/")

@app.route("/services/service_view/<int:serviceid>")
def service_view(serviceid): 
    service = Utility.service_view(serviceid)
    if service: 
        return redirect(service.url)
    return redirect("/")

"""
@app.route("/services/service_start/<servicename>")
def service_start(servicename): 
    Utility.service_start(servicename)
    return redirect("/")

@app.route("/services/service_stop/<servicename>")
def service_stop(servicename): 
    Utility.service_stop(servicename)
    return redirect("/")
"""

@app.route("/<servicename>")
def service_router(servicename):
    service = Utility.service_start(servicename)
    if not service:
        return "Service not found"
    return f"{service.name} is {servicename}"

def home_insital():    
    Utility.services_register(SERVICES_PATH, servicePort)    
    Utility.user_signup(Config.ADMIN_NAME, Config.ADMIN_PASSWORD, True, True)
    
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
        home_insital()    
    app.run(port=servicePort, debug=False, use_reloader=False)
