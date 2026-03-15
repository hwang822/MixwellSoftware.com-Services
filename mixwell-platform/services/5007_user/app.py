import os
import sys
from flask_login import LoginManager
from flask import Flask, render_template

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#if BASE_DIR not in sys.path:
#    sys.path.insert(0, BASE_DIR)
#from settings import Config
#from auth.models import db, Utility, User, UserService
#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
#sys.path.insert(0, BASE_DIR)
app = Flask(__name__)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(servicePort)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader

#serviceName = "UserService"

# ---------- Login, siginup, logout ROUTES ----------

@app.route("/")
def home():    
#    print(f"Welcome {user['email']} using {user['servicename']}")
#    username = user['email']
#    userid = user['userid']
#    userswithservices =  Utility.user_with_services(userid)
#    return render_template("UserService.html", username = username, userswithservices = userswithservices)                         
    return render_template(f"{serviceName}.html", username = "Test")
    
if __name__ == "__main__":
    app.run(port=servicePort, debug=False, use_reloader=False)
