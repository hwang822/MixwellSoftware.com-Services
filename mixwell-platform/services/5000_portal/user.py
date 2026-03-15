"""
import os
import sys
from flask_login import LoginManager, logout_user, login_required
import jwt # install PyJWT
from flask import Flask, flash, make_response, redirect, render_template, request, session
from models import Utility,  User

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#if BASE_DIR not in sys.path:
#    sys.path.insert(0, BASE_DIR)
#from settings import Config
#from auth.models import db, Utility, User, UserService
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import db, Utility, User
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

serviceName = "UserService"
authUrl = f"http://{Config.SERVICE_URL}:{Config.PORTAL_PORT}/login?next=http://{Config.SERVICE_URL}:{Config.PORTAL_PORT}"

# ---------- Login, siginup, logout ROUTES ----------

currentuser = None
@app.route("/")
def home():
    token = request.cookies.get("access_token")
    if not token:
        print(authUrl)         
        return redirect(authUrl)
    user = Utility.user_bytoken(token)
    userswithservices =  Utility.user_with_services(user.id)
    return render_template("user_dashboard.html", user = user, userswithservices = userswithservices)                     
    
if __name__ == "__main__":
    app.run(port=Config.PORTAL_PORT, debug=False, use_reloader=False)
"""