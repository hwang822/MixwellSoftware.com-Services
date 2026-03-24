import sys
from flask import Flask, Response, redirect
import requests

app = Flask(__name__)

BASE_DIR = f"{app.root_path}/../../"  
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from models import Utility, db

serviceport = int(Config.GATEWAY_PORT)
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

portalport = int(serviceport/1000)*1000
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/auth_{portalport}"

@app.route("/")
def home():
    serviceurl = f"{Config.SERVICE_URL}:{portalport}"
    r = requests.get(f"{serviceurl}/user")  #"http://localhost:8000/user"
    return Response(r.content, r.status_code, r.headers.items())

@app.route("/service/<servicename>")  #services.mixwellsoftware.com/service/servicename
def route_service(servicename):
    service = Utility.service_get(servicename)
    r = requests.get(f"{service.url}/{servicename}")  #"http://127.0.0.1:5001/ai"
    return Response(r.content, r.status_code, r.headers.items())


    try:
        # ✅ 1. 验证用户
        user = Utility.user_check(servicename)    
        if not user:
            r = requests.get(f"{serviceport}/login?next={serviceurl}/service/{servicename}")
            return Response(r.content, r.status_code, r.headers.items())

        # ✅ 2. 查 service 信息（DB）
        service = Utility.service_get(servicename)
        if not service:
            return "Service not found", 404

        r = requests.get(f"{serviceurl}:{serviceport}")  #"http://localhost:8000/user"
        return Response(r.content, r.status_code, r.headers.items())
        
    except Exception as e:
        print (f"Requests errors: {e}")
        #Utility.notify_support(service, str(e))        
        return "Sorry, service is not available at the moment", 500

if __name__ == "__main__":
    with app.app_context(): 
        app.config["SQLALCHEMY_DATABASE_URI"] = auth_db 
        db.init_app(app)    
    print (f"run gateway service at {serviceport}")    
    app.run(port=serviceport, debug=False, use_reloader=False)
