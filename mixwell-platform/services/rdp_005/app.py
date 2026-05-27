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
servicename = "AI"
app.config["SQLALCHEMY_DATABASE_URI"] = f"cam_{serviceport}" 
#db.init_app(app)

#app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 

rdpService = Blueprint("registryService", __name__)
@rdpService.route("/")
def home():    
    return render_template(f"rdp.html", servicename = "RDP Service")        

def create_app():
    app.register_blueprint(rdpService)
    return app
if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host=Config.SERVICE_BIND_HOST_INTERNAL, port=serviceport)