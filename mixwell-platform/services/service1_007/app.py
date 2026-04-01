import os, sys
from flask import Blueprint, Flask, render_template
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from models import db

app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')
shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport

#app.config["SQLALCHEMY_DATABASE_URI"] = f"cam_{serviceport}" 
#db.init_app(app)

servicename = "Service1"  
servicedb = f"{Config.SQLALCHEMY_DATABASE_URI}/{servicename}_{serviceport}"

#serviceport = int(sys.argv[1])
#servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb.lower()}" 
db.init_app(app)

"""
app = Flask(__name__)

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]
"""
#app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 
#db.init_app(app)

service1Service = Blueprint("service1Service", __name__)
@service1Service.route("/")
def home():    
    return render_template(f"{servicename.lower()}.html", servicename = f"{servicename} Service")        

def create_app():
    app.register_blueprint(service1Service)
    return app

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)
