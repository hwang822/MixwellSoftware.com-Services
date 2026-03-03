import os
from dotenv import load_dotenv
from flask import Blueprint, Flask, redirect, request
import jwt
import requests

# Load .env from project root
load_dotenv()

class Config:
    JWT_SECRET = os.getenv("JWT_SECRET")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL = os.getenv("EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    VERIFY_URL = os.getenv("VERIFY_URL")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    JWT_SECRET = os.getenv("JWT_SECRET")
    AUTH_PORT = os.getenv("AUTH_PORT")
    AUTH_URL = os.getenv("AUTH_URL")

class Utility:

    def create_app(service, servicePort, db):
        app = Flask(__name__)
        app.register_blueprint(service)
        app.config.from_object(Config)
        db.init_app(app)
        with app.app_context():        
            db.create_all()    
        app.run(port=servicePort)  


    def service_user_auth(serviceName, serviceDesc, serviceUrl, servicePort):
        token = request.cookies.get("access_token")

        if not token:
            routepath = f"{Config.AUTH_URL}:{Config.AUTH_PORT}/user/signup"
            return routepath

        else:
            decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            user_id = decoded["user_id"]    

            payload ={
                "servicename": serviceName,
                "servicedesc": serviceDesc,
                "url": serviceUrl,
                "port": servicePort,
                "userid" : user_id
            }
        
            routepath = f"{Config.AUTH_URL}:{Config.AUTH_PORT}/user/verified"
            return routepath
        
            response = requests.post(
                routepath,
                json=payload
            )        
            
            if response.status_code == 200:
                return ""         
            else:
                routepath = f"{Config.AUTH_URL}:{Config.AUTH_PORT}/user/login"
                return routepath
