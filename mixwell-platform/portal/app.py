import subprocess
import sys
from flask_login import LoginManager, logout_user
from flask import Flask, flash, make_response, redirect, render_template, request, send_file
import requests

from flask_migrate import Migrate, upgrade, init, migrate as migrate_cmd
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

serviceport = int(Config.PORTAL_PORT)
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 
print (f"Portal Service port# {serviceport}")

servicedb = "auth"  
serviceName = "portal"

dbname = f"{servicedb}_{serviceport}"
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/{dbname}"

SERVICES_PATH = f"{BASE_DIR}\\services"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
@app.route("/")
def home():
    services = Utility.services_get_all()
    user = Utility.user_check("")
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
    #ip = request.headers.get('X-Forwarded-For', request.remote_addr),        
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
"""
@app.route("/service/<servicename>")
def serivce_access(servicename):
    user = Utility.user_check(servicename)    
    if not user:
        return redirect(f"/login?next=/service/{servicename}")    
    service = Utility.service_get(servicename)
    if not service:
        return f"{servicename} service is not avalaible!"
    return redirect(f"{service.url}")
"""
@app.route("/service/<servicename>")
def route_service(servicename):
    try:
        # ✅ 1. 验证用户
        user = Utility.user_check(servicename)    
        if not user:
            return redirect(f"/login?next=/service/{servicename}")    

        if not user:
            return redirect("/login")

        # ✅ 2. 查 service 信息（DB）
        service = Utility.service_get(servicename)
        if not service:
            return "Service not found", 404
        return redirect(f"{service.url}")

        # ✅ 3. 记录访问
        #record_user_service(user.id, service.id)
            #did at 1. 验证用户

        # ✅ 4. 转发（proxy）
        # url = service.url   # e.g. http://localhost:8001
        # resp = requests.get(url, cookies=request.cookies)

        #return resp.text

    except Exception as e:
        Utility.notify_support(service, str(e))
        return "Sorry, service is not available at the moment", 500

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

@app.route("/services/service_download/<servicename>")
def service_download(servicename):     
    return render_template("servicedownload.html", servicename = servicename)

@app.route("/services/download/win/<servicename>")
def download_win(servicename):
    return send_file(
        f"static/downloads/app_{servicename}.exe",
        as_attachment=True
    )

@app.route("/services/download/ios")
def download_ios():
    return "Redirect to PWA or App Store"

@app.route("/services/download/android/<servicename>")
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
    Migrate(app, db)

    # ⭐ 自动处理 migrations
    migrations_dir = os.path.join(os.getcwd(), "migrations")

    with app.app_context():
        if not os.path.exists(migrations_dir):
            print("Initializing migrations...")
            init()
            migrate_cmd(message="init")
        upgrade()

    Utility.services_register(SERVICES_PATH, serviceport)    
    user = Utility.user_signup(
        Config.ADMIN_NAME,
        Config.ADMIN_PASSWORD,
        True,
        True
    )
if __name__ == "__main__":
    with app.app_context():        
        home_insital()    
    print (f"run portal poat at {serviceport}")    
    app.run(port=serviceport, debug=False, use_reloader=False)
