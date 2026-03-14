import os
import sys
from flask_login import LoginManager, logout_user, login_required
import jwt # install PyJWT
from flask import Flask, flash, make_response, redirect, render_template, request, session
from models import Utility, db, Utility, User

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

SERVICES_PATH = f"{BASE_DIR}\services"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

serviceName = "PortalService"
serviceUrl =  Config.SERVICE_URL
servicePort = Config.PORTAL_PORT

# ---------- Login, siginup, logout ROUTES ----------

@app.route("/")
def home():
    token = request.cookies.get("access_token")
    services = Utility.services_get_all()
    if not token:
        return redirect("/logout")
    try:
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        userid = decoded["userid"]
        currentuser = Utility.user_get(userid)
        userswithservices =  Utility.user_with_services(currentuser.id)
        if currentuser.is_admin:
            users = Utility.users_get_all()
            userswithoutservices =  Utility.user_without_services(currentuser.id)    
            return render_template("admin_dashboard.html", services = services, users = users, userswithservices = userswithservices, userswithoutservices=userswithoutservices)     
        else:
            return render_template("user_dashboard.html", user = currentuser, userswithservices = userswithservices)                     
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
    session.pop('_flashes', None)
    logout_user()
    return redirect("/login")

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
    return redirect(service.url)

@app.route("/services/service_start/<int:serviceid>")
def service_start(serviceid): 
    Utility.service_start(serviceid)
    return redirect("/")

@app.route("/services/service_stop/<int:serviceid>")
def service_stop(serviceid): 
    Utility.service_stop(serviceid)
    return redirect("/")

def home_insital():
    Utility.services_register(SERVICES_PATH)
    Utility.user_signup(Config.ADMIN_NAME, Config.ADMIN_PASSWORD, True, True)
    
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
        home_insital()    
    app.run(port=servicePort, debug=False, use_reloader=False)
