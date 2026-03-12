from flask import Flask, Blueprint, render_template
import os
import sys
from flask import Flask, Blueprint

BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5008
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')

registryService = Blueprint("registryService", __name__)

SERVICES = []
@registryService.route("/", methods=["POST"])
def register_home():
    register()

@registryService.route("/register", methods=["POST"])
def register():

    service={
        "name": "AI Service",
        "url": "http://localhost:8001\health"
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
    create_app().run(host="127.0.0.1", port=BASE_PORT) 
