import os, sys
from flask import Flask, redirect, render_template, request, url_for
import requests
from models import db

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import db, Utility
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

serviceName = "service1"
serviceDesc = "service 1"
serviceUrl = "localhost"
servicePort = "5010"
authPort = 5000
authUrl = f"http://{serviceUrl}:{authPort}/login?next=http://{serviceUrl}:{servicePort}"
@app.route("/")
def home():    
    token = request.cookies.get("access_token")
    if not token:
        print(authUrl)         
        return redirect(authUrl)
    return render_template(f"{serviceName}.html")    
    
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
        Utility.service_add(serviceName, serviceDesc, serviceUrl, servicePort)
    app.run(port=servicePort)
