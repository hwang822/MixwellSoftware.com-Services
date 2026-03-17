import os
import sys
from flask import Flask, render_template
from flask_login import LoginManager


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from models import Utility, db, Utility, User

app = Flask(__name__)

app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(sys.argv[1]) if len(sys.argv) > 1 else int(servicePort)

@app.route("/user/<int:userid>")
def home(userid):    
    user = Utility.user_get(userid)
    userswithservices =  Utility.user_with_services(userid)
    return render_template(f"{serviceName}.html", username = user.email, user_with_services = userswithservices)
    
if __name__ == "__main__":
    app.run(port=servicePort, debug=False, use_reloader=False)
