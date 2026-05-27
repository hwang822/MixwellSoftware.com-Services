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

registryService = Blueprint("registryService", __name__)

SERVICES = []
@registryService.route("/")
def register_home():
    return register() 

@registryService.route("/register", methods=["POST"])
def register():

    service={
        "name": "AI Service",
        "url": "http://localhost:8001"
    }
    SERVICES.append(service)
    service={
        "name": "Cam Service",
        "url": "http://localhost:8002"
    }
    SERVICES.append(service)
    service={
        "name": "Video Service",
        "url": "http://localhost:8003"
    }
    SERVICES.append(service)
    service={
        "name": "Email Service",
        "url": "http://localhost:8004"
    }
    SERVICES.append(service)
    service={
        "name": "Travel Service",
        "url": "http://localhost:8005"
    }
    SERVICES.append(service)
    service={
        "name": "Data API Service",
        "url": "http://localhost:8006"
    }
    SERVICES.append(service)
    service={
        "name": "RDP Service",
        "url": "http://localhost:8007"
    }
    SERVICES.append(service)
    return {"status": "registered"}

@registryService.route("/services")
def services():
    register()
    return SERVICES

def create_app():
    app = Flask(__name__)
    app.register_blueprint(registryService)
    return app


if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host=Config.SERVICE_BIND_HOST_INTERNAL, port=serviceport) 

