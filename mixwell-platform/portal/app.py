import sys
from flask_login import LoginManager, login_user, logout_user
from flask import Blueprint, Flask, flash, make_response, redirect, render_template, request, send_file, session

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

serviceport = int(Config.PORTAL_PORT)
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 
print (f"Portal Service port# {serviceport}")

servicedb = "auth"  
serviceName = "portal"

dbname = f"{servicedb}_{serviceport}"
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/{dbname}"

SERVICES_PATH = f"{BASE_DIR}\\services"
app.config['SECRET_KEY'] = 'same-key-for-all-services'

portalService = Blueprint("portalService", __name__)

@portalService.route("/")
def home(): #insde user visit 5000
    services = Utility.services_get_all()
    user = Utility.user_check_only()
    if not user:
        return render_template("portal.html", services = services)    
    try:
        if user.is_admin:
            users = Utility.users_list()
            return render_template("admin_dashboard.html", services = services, users = users)     
        else:
            userswithservices =  Utility.user_with_services(user.id)
            return render_template("user.html", username = user.email, user_with_services = userswithservices)
    except Exception as e:
        print (e)
        return render_template("portal.html", services = services)     

# -------------------------
# user signup, login, logout request from auth UI 
# -------------------------
@portalService.route("/signup", methods=["GET", "POST"])  
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

@portalService.route("/login", methods=["GET", "POST"])
def login():          
    if request.method == "GET":                
        return render_template("login.html")
    session.pop('_flashes', None)                
    email = request.form["username"]
    password = request.form["password"]    
    #ip = request.headers.get('X-Forwarded-For', request.remote_addr),        
    response = Utility.user_login(email, password)    
    flash(response["message"])
    if response["status"] == 400:
        return redirect("/login")
    else :  
        flash(response["message"])
        currentuser = response["data"]
        login_user(currentuser)        
        next_url = request.args.get("next")
#        servicename = request.args.get("service")
        token = Utility.user_token(currentuser)                                
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

@portalService.route("/logout", methods=["GET", "POST"])
def logout():    
    logout_user()
    session.pop('_flashes', None)                
    services = Utility.services_get_all()
    return render_template("portal.html", services = services)     

# -------------------------
# admin request from  admin_dashboard UI
# -------------------------

@portalService.route("/admin/user_remove/<int:userid>") 
def user_remove(userid):
    Utility.user_remove(userid)
    return redirect("/")

@portalService.route("/admin/user_approve/<int:userid>")
def user_approve(userid):
    Utility.user_approve(userid)
    return redirect("/")

@portalService.route("/admin/user_verify/<token>")
def user_verify(token):
    user = Utility.user_verify(token)
    return (f"user {user.email} has been approved!")

@portalService.route("/admin/user_add_service", methods=["POST"])
def user_add_service():
    userid = request.form.get("userid")
    serviceid = request.form.get("serviceid")
    Utility.user_add_service(userid, serviceid)
    return redirect("/")    

@portalService.route("/admin/user_remove_service", methods=["POST"])
def user_remove_service():
    userid = int(request.form.get("userid"))
    serviceid = int(request.form.get("serviceid"))
    Utility.user_remove_service(userid, serviceid)
    return redirect("/")    

@portalService.route("/admin/service_remove/<int:serviceid>")
def service_remove(serviceid):
    Utility.service_remove(serviceid)
    return redirect("/")

# -------------------------
# service app download request from home and servicedownload UI 
# -------------------------

@portalService.route("/servicedownload/<servicename>")
def service_download(servicename):     
    return render_template("servicedownload.html", servicename = servicename)

@portalService.route("/servicedownload/win/<servicename>")
def download_win(servicename):
    return send_file(
        f"static/downloads/app_{servicename}.exe",
        as_attachment=True
    )

@portalService.route("/servicedownload/ios")
def download_ios():
    return "Redirect to PWA or App Store"

@portalService.route("/servicedownload/android/<servicename>")
def download_android(servicename):
    return send_file(
        f"static/downloads/app_{servicename}.apk",
        as_attachment=True
    )

def home_insital():
    dbname = f"auth_{serviceport}"        
    Utility.create_service_database(dbname)   
    app.config["SQLALCHEMY_DATABASE_URI"] = auth_db 
    db.init_app(app)            
    db.create_all()
    
    Utility.services_register(SERVICES_PATH, serviceport)    
    Utility.user_signup(
        Config.ADMIN_NAME,
        Config.ADMIN_PASSWORD,
        True,
        True
    )

def create_app():
    app.register_blueprint(portalService)
    return app

if __name__ == "__main__":
    with app.app_context():        
        home_insital()    
    print (f"run portal poat at {serviceport}")    
    create_app().run(host="0.0.0.0", port=serviceport)
