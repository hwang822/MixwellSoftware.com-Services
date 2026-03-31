import os
import sys
from flask import Blueprint, Config, Flask, render_template
from flask_login import LoginManager

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')

shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from models import Utility, db, User

serviceport = int(app.root_path.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 
servicename = "User Service"  
#servicedb = f"{Config.SQLALCHEMY_DATABASE_URI}/{servicename}_{serviceport}"


#app = Flask(__name__)
#BASE_DIR = f"{app.root_path}/../../"  
#sys.path.insert(0, BASE_DIR)
#from models import Utility, db, User, Config

#serviceport = int(sys.argv[1])
#servicedb = sys.argv[2]

#serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 
serviceurl = f"{Config.SERVICE_URL}:{serviceport}"
portalport = int(serviceport/1000)
portalport = portalport*1000
authurl = f"{Config.SERVICE_URL}:{portalport}"
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/auth_{portalport}"

app.config["SQLALCHEMY_DATABASE_URI"] = f"{auth_db}" 

#app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

userService = Blueprint("userService", __name__)
@userService.route("/")
def home():
    try:    
        return render_template("user.html", servicename = servicename)
    except Exception as e:
        print (e)
        return e

@userService.route("/user/<int:userid>")
def userhome(userid):    
    user = Utility.user_get(userid)
    userswithservices =  Utility.user_with_services(userid)
    return render_template("user.html", username = user.email, user_with_services = userswithservices, servicename = servicename)
    
def create_app():
    app.register_blueprint(userService)
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport, debug=False, use_reloader=False)
