import os
import sys
from flask import Flask, redirect, render_template, request
import jwt
import requests

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
from config.settings import Config

class Utiliy:
    def create_app(serviceName, db):
        app = Flask(__name__)
        with app.app_context():        
            db.create_all()    
        app.register_blueprint(serviceName)
        app.config.from_object(Config)
        db.init_app(app)
        return app    

    def service_user_auth(serviceName, serviceDesc, serviceUrl, servicePort):
        token = request.cookies.get("access_token")
        if not token:
            authPath = Config.AUTH_URL + ":" + Config.AUTH_PORT + "/user/signup"
            return redirect(authPath)

        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user_id = decoded["user_id"]    
        payload ={
            "servicename": serviceName,
            "servicedesc": serviceDesc,
            "url": serviceUrl,
            "port": servicePort,
            "userid" : user_id
        }

        authPath = Config.AUTH_URL + ":" + Config.AUTH_PORT + "/user/verified"
        response = requests.post(
            authPath,
            json=payload
            )        
        
        return response
"""    
    if response.status_code == 200:
        return render_template(f"{serviceName}.html")        
    else:
        authPath = Config.AUTH_URL + ":" + Config.AUTH_PORT + "/user/login"
        return redirect(authPath)
"""
