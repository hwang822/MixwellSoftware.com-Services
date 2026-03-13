import os, sys
from flask import Flask, redirect, render_template, request, url_for
#import requests
#from models import db

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import db, Utility
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, servicename = folder_name.split("_", 1)
servicePort = int(servicePort)

authUrl = f"http://{Config.SERVICE_URL}:{Config.PORTAL_PORT}/login?next=http://{Config.SERVICE_URL}:{servicePort}"
@app.route("/")
def home():    
    token = request.cookies.get("access_token")
    if not token:
        print(authUrl)         
        return redirect(authUrl)
    user = Utility.user_bytoken(token)
    service = Utility.user_add_service_byname(user.id, servicename)    
    return render_template(f"{servicename}.html")    
    
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=servicePort)
