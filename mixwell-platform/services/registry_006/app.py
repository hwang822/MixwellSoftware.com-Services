from flask import Flask, Blueprint
import sys

app = Flask(__name__)

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 

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
    create_app().run(host="127.0.0.1", port=serviceport) 

