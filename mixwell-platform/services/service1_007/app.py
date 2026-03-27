import sys
from flask import Blueprint, Flask, render_template

from models import db
app = Flask(__name__)

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 
db.init_app(app)

service1Service = Blueprint("service1Service", __name__)
@service1Service.route("/")
def home():    
    return render_template("service1.html")        

def create_app():
    app.register_blueprint(service1Service)
    return app

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)
