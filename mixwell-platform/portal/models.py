from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
import os
import smtplib
import sys
from flask import render_template
import jwt
from sqlalchemy import and_, true
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from config.settings import Config

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
            service = Service(   # new service
                name = name,
                desc=desc,
                url=url,
                port=port,
                started_at=datetime.now(timezone.utc) + timedelta(hours=12)
            )
            db.session.add(service)                
            db.session.commit()
        return service        

    def service_remove(serviceid):
        Service.query.filter_by(id=serviceid).delete()
        UserService.query.filter_by(service_id=serviceid).delete()
        db.session.commit()
        return serviceid

    def service_start(serviceid):
        service = Service.query.get_or_404(serviceid)
        return service
            

# users methods

    def user_signup(email, password, is_verified, is_admin):         
        user = User.query.filter_by(email=email).first()   
        if user is None:
            user = User(
                email = email, 
                password= generate_password_hash(password), 
                is_verified = is_verified,
                is_admin = is_admin,
                created_at = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())            
            )
            db.session.add(user)                
            db.session.commit()
            try:
                if is_verified == False:
                    Utility.user_verify_email(user.id, email)
                return Utility.auth_response(200, "New User signup scussfully!", user)
            except:                                            
                return Utility.auth_response(400, "Invalid Eamil.", user)
        else:
            return Utility.auth_response(400, "Username already exists.", user)
            
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
        return userid

    def user_approve(userid):
        user = User.query.get_or_404(userid)
        user.is_verified = True
        db.session.commit()        
        return user

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
        return user            
    
    def user_verify_email(user_id, user_email):    
        token = Utility.user_token(user_id)
        verify_url = Config.VERIFY_URL + f"/{token}"
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

        # Zoho mail service using SMTP_SSL
        smtp = smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT)
        smtp.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
        try:
            smtp.sendmail(
                    Config.SMTP_EMAIL,
                    user_email,
                    message.as_string()
                )
            smtp.quit()
            return {"status": 200, "message": f"Verify Email has been sent to {user_email}"}            
        except:
            return {"status" : 401,"message" : "Invalid email address"}         

        """    
        # ✅ gmail service useing SMTP
        smtp = smtplib.SMTP(Config.SMTP_SERVER_G, Config.SMTP_PORT_G)
        smtp.starttls()
        smtp.login(Config.SMTP_EMAIL_G, Config.SMTP_PASSWORD_G)
        try:
            smtp.send_message(message)            
            smtp.quit()
            print(f"Verify Email has been sent to {user_email}")
            return {"status": 200, "message": f"Verify Email has been sent to {user_email}"}            
        except smtplib.SMTPRecipientsRefused:            
            print("Invalid email address")   
            return {"status" : 401,"message" : "Invalid email address"}         
        """

    def user_token(user_id):
        # Generate JWT token
        payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=12)
        }
        token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
        return token


    def user_add_service(userid, serviceid): #update users_services table for connect user.id and service.id        
        service = Service.query.filter_by(id=serviceid).first()
        userservices = UserService.query.filter_by(   
            user_id=userid,
            service_id=serviceid
        ).first()

        if not userservices:
            userservices = UserService(
                user_id=userid,
                service_id=serviceid,
                access = 1
            )
            db.session.add(userservices)
            db.session.commit()
        return userservices

    def user_remove_service(user_id, service_id):  
        userService = UserService.query.filter_by(
            user_id=user_id,
            service_id=service_id
        ).first()
        db.session.delete(userService)
        db.session.commit()    

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
        return results

    def user_without_services(userid):        
        results = []
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
        return results

    def services_add_all(services):
        for service in services:
            Utility.service_add(service["name"], service["desc"], service["url"], service["port"])

    def auth_response(status, message, data):
        return {"status" : status, "message" : message, "data" : data}

