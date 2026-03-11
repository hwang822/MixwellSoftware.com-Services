from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
import os
import smtplib
import sys
from flask import flash, jsonify, make_response, redirect, render_template, request
import jwt
from sqlalchemy import and_, true
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy
#from email_service import user_token

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from config.settings import Config

#from settings import Config


class User(UserMixin, db.Model):   # Set UserMixin for flask_login import LoginManager login_user(user) check
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "password": self.password,
            "is_admin": self.is_admin,
            "is_verified": self.is_verified,
            "created_at": self.created_at
        }    

class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    desc = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "desc": self.desc,
            "url": self.url,
            "port": self.port,
            "started_at": self.started_at
        }    

class UserService(db.Model):
    __tablename__ = "users_services"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    service_id = db.Column(db.Integer)
    access = db.Column(db.Integer)

class Utility:

# service methods
    def services_get_all():
        return Service.query.all()

    def service_add(name, desc, url, port):
        service = Service.query.filter_by(name=name).first()  # serviceName is unique      
        if service is None:
            s = Service(   # new service
                name = name,
                desc=desc,
                url=url,
                port=port,
                started_at=datetime.now(timezone.utc) + timedelta(hours=12)
            )
            db.session.add(s)                
            db.session.commit()        

    def service_remove(serviceid):
        Service.query.filter_by(id=serviceid).delete()
        UserService.query.filter_by(service_id=serviceid).delete()
        db.session.commit()

# users methods

    def user_signup(email, password, is_verified, is_admin):         
        user = User.query.filter_by(email=email).first()   
        password = generate_password_hash(password) # password hash        
        if user is None:
            user = User(
                email = email, 
                password= password, 
                is_verified = is_verified,
                is_admin = is_admin,
                created_at = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())            
            )
            db.session.add(user)                
            db.session.commit()
            response = Utility.user_verify_email(user.id, email)                            
            return response            
        else:
            if is_admin == true:
                user.password = password
                user.is_verified = is_verified
                user.is_admin = is_admin
                db.session.add(user)                
                db.session.commit()
            return {
                "status": 400, 
                "message": "Username already exists."}
            
    def user_login(email, password):         
        user = User.query.filter_by(email=email).first()                
        if user is None:
            return Utility.auth_response(400, "Invalid username.", user)
        elif not check_password_hash(
            user.password, 
            password):
            return Utility.auth_response(400, "Invalid password.", user)
        elif user.is_verified == False:
            return Utility.auth_response(400, "Waitting verify email for approve.", user)
        else:
            login_user(user)
            return Utility.auth_response(200, "Login Scussfully!", user)

    def users_get_all():
        return User.query.all()

    def user_get(userid):         
        user = User.query.filter_by(id=userid).first()
        return user
                
    def user_remove(userid):
        User.query.filter_by(id=userid).delete()
        UserService.query.filter_by(user_id=userid).delete()
        db.session.commit()

    def user_approve(userid):
        user = User.query.get_or_404(userid)
        if not user.is_admin:
            return "Access denied", 403
        user = User.query.get(userid)
        user.is_approved = True
        db.session.commit()
        return

    def user_verify(token):
        decoded = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id = decoded["user_id"]
        user = User.query.filter_by(id=user_id).first()
        if user.is_verified == False:
            user.is_verified = True
            db.session.commit()
        return {
            "status": 200, 
            "error": "User is verified."}            

    def user_auth(serviceName):
        token = request.cookies.get("access_token")
        if not token:
            return redirect("/login")
        try:
            decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            userid = decoded["user_id"]
            user = Utility.user_get(userid)
            if user.is_verfied:
                token = jwt.encode({"user_id": user["id"], "service": serviceName}, Config.JWT_SECRET, algorithm="HS256")
                resp = make_response({"status": "ok"})
                resp.set_cookie(f"{serviceName}_token", token)
                return user
            else:
                return None 
        except Exception:
            return None
        
    def user_verify_email(user_id, user_email):    
        token = Utility.user_token(user_id)
        verify_url = Config.VERIFY_URL + f"{token}"
        html_content = render_template(
            "verify_email.html",
            user_email=user_email,
            verify_url=verify_url
        )

        # ✅ Create proper MIME message
        message = MIMEText(html_content, "html")
        message["Subject"] = "Verify Your Email"
        message["From"] = Config.SMTP_EMAIL
        message["To"] = user_email
        smtp = smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT)
        smtp.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
        smtp.sendmail(
                Config.SMTP_EMAIL,
                user_email,
                message.as_string()
            )
        smtp.quit()

        # ✅ Use SMTP correctly   
        smtp = smtplib.SMTP(Config.SMTP_SERVER_G, Config.SMTP_PORT_G)
        smtp.starttls()
        smtp.login(Config.SMTP_EMAIL_G, Config.SMTP_PASSWORD_G)
        try:
            smtp.send_message(message)            
            smtp.quit()
            print(f"Verify Email has been sent to {user_email}")
            return {
                "status": 200, 
                "message": f"Verify Email has been sent to {user_email}"}            
        except smtplib.SMTPRecipientsRefused:            
            print("Invalid email address")   
            return {
                "status" : 401,
                "message" : "Invalid email address"
            }         

    def user_token(user_id):
        # Generate JWT token
        payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=12)
        }
        token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
        return token


    def user_add_service(userid, servicename): #update users_services table for connect user.id and service.id        
        service = Service.query.filter_by(name=servicename).first()

        userservices = UserService.query.filter_by(   
            user_id=userid,
            service_id=service.id
        ).first()

        if not userservices:
            userservices = UserService(
                user_id=userid,
                service_id=service.id,
                access = 1
            )
            db.session.add(userservices)
            db.session.commit()

    def user_remove_service(user_id, service_id):  
        results = (
            db.session.query(User, UserService)
            .join(UserService, UserService.userid == user_id)        
            .all()
        )
        userServices = UserService.query.filter_by(
            userid=user_id,
            serviceid=service_id
        ).all()

        for userService in userServices:        
            db.session.delete(userService)
            db.session.commit()    
        return 

    def user_with_services(userid):
        results = (        
            db.session.query(
                    UserService.user_id,
                    Service.id,
                    Service.name
                )
                .join(Service, UserService.service_id == Service.id)
                .all()
        )

        response = [
        {
            "userid": r.user_id,
            "serviceid": r.id,
            "servicename": r.name
        }
        for r in results
        ]
        return response
    

    def user_without_services(userid):        
        results = []
        if UserService.query.count()>0:
            results = (
                db.session.query(
                    User.id.label("userid"),
                    Service.id.label("serviceid"),
                    Service.name
                )
                .join(Service, true())   # cross join
                .outerjoin(
                    UserService,
                    and_(
                        UserService.id == User.id,
                        UserService.id == Service.id
                    )
                )
                .filter(UserService.id == None)
                .all()
            )

        response = [
            {
                "userid": r.userid,
                "serviceid": r.serviceid,
                "servicename": r.name
            }
            for r in results
        ]
        return response

    def services_add_all(services):
        for service in services:
            Utility.service_add(service["name"], service["desc"], service["url"], service["port"])

    def auth_response(status, message, data):
        return {"status" : status, "message" : message, "data" : data}

