import os, sys
from flask import Flask, redirect, render_template, request
import jwt

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import db
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(servicePort)
authUrl = f"{Config.SERVICE_URL}:{Config.PORTAL_PORT}/login?service={serviceName}&next={Config.SERVICE_URL}:{servicePort}"
@app.route("/")
def home():    
    user =  get_user()
    if not user:
        return redirect(authUrl) 
    print(f"Welcome {user['email']} using {user['servicename']}")
    return render_template(f"{serviceName}.html") 

def get_user():     
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user = f"{payload['userid']} + {payload['email']} + {payload['servicename']}"
    except:
        return None        
    return payload
       
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=servicePort)

