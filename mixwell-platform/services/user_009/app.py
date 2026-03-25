import sys
from flask import Config, Flask, render_template
from flask_login import LoginManager

app = Flask(__name__)
BASE_DIR = f"{app.root_path}/../../"  
sys.path.insert(0, BASE_DIR)

from models import Utility, db, User, Config

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]

serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 
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

@app.route("/")
def home():
    try:    
        return render_template("user.html")
    except Exception as e:
        print (e)
        return e

@app.route("/user/<int:userid>")
def userhome(userid):    
    user = Utility.user_get(userid)
    userswithservices =  Utility.user_with_services(userid)
    return render_template("user.html", username = user.email, user_with_services = userswithservices)
    
if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    app.run(port=serviceport, debug=False, use_reloader=False)
