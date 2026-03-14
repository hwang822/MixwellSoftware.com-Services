import os
import sys
from flask_login import LoginManager, logout_user, login_required
#import jwt # install PyJWT
from flask import Flask, flash, make_response, redirect, render_template, request, session

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#if BASE_DIR not in sys.path:
#    sys.path.insert(0, BASE_DIR)
#from settings import Config
#from auth.models import db, Utility, User, UserService
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import Utility
app = Flask(__name__)
app.config.from_object(Config)
#db.init_app(app)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(servicePort)
authUrl = f"{Config.SERVICE_URL}:{Config.PORTAL_PORT}/login?service={serviceName}&next={Config.SERVICE_URL}:{servicePort}"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#serviceName = "UserService"
authUrl = f"http://{Config.SERVICE_URL}:{Config.PORTAL_PORT}/login?next=http://{Config.SERVICE_URL}:{Config.PORTAL_PORT}"

# ---------- Login, siginup, logout ROUTES ----------

currentuser = None
@app.route("/")
def home():    
#    print(f"Welcome {user['email']} using {user['servicename']}")
#    username = user['email']
#    userid = user['userid']
#    userswithservices =  Utility.user_with_services(userid)
#    return render_template("UserService.html", username = username, userswithservices = userswithservices)                     
    return render_template(f"{serviceName}.html")
    
if __name__ == "__main__":
    app.run(port=servicePort, debug=False, use_reloader=False)
