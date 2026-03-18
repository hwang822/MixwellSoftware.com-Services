import os
import sys
from flask import Flask, render_template
from flask_login import LoginManager
from models import Utility, db, Utility, User

app = Flask(__name__)

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 

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
    return render_template("user.html")

@app.route("/user/<int:userid>")
def userhome(userid):    
    user = Utility.user_get(userid)
    userswithservices =  Utility.user_with_services(userid)
    return render_template("user.html", username = user.email, user_with_services = userswithservices)
    
if __name__ == "__main__":
    app.run(port=serviceport, debug=False, use_reloader=False)
