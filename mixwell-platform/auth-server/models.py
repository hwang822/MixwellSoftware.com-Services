from datetime import datetime, timedelta, timezone
from flask import jsonify, make_response, redirect, request
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy

from email_service import user_token

db = SQLAlchemy()

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
        service = Service.query.get_or_404(serviceid)
        if service is None:
            userservices = UserService.query.filter_by(service.id)   
            if userservices is not None:
                db.session.delete(userservices)        
                db.session.commit()

    def services_get_all():
        services = Service.query.all()
        servicesJson = jsonify([s.to_dict() for s in services])
        return servicesJson

    def user_signup(email, password, is_verified, is_admin):         
        user = User.query.filter_by(email=email).first()        
        password= generate_password_hash(password)
        if user is None:
            user = User(
                email = email, 
                password= password, # password hash
                is_verified = is_verified,
                is_admin = is_admin,
                created_at = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())            
            )
            db.session.add(user)                
            db.session.commit()
            return {"error": "Signup successful."}, 200    
        else:
            user.password = password
            user.is_verified = is_verified
            user.is_admin = is_admin
            db.session.add(user)                
            db.session.commit()
            return {"error": "Username already exists."}, 401
            
    def user_login(email, password):         
        user = User.query.filter_by(email=email).first()                
        if user is None:
            #flash("Invalid username!.")
            return {"error": "Invalid username!."}, 401
        elif not check_password_hash(
            user.password, 
            password):
            return {"error": "Invalid password!."}, 401    
        elif user.is_verified == False:
            #flash("Waitting verify email for approve.")
            return {"error": "Waitting verify email for approve."}, 401    
        else:
            #flash("Login successful!")
            token = user_token(user.id)
            next_url = request.args.get("next")  #next url from send server
            response = make_response(
                redirect(next_url)
            )
            response.set_cookie(
                "access_token",
                token,
                httponly=True,
                samesite="Lax"
            )
            login_user(user)                        
            return {"error": "Login successful."}, 200    

    def user_remove(userid):
        user = User.query.get_or_404(userid)
        if user is not None:
            db.session.delete(user)   
            userservices = UserService.query.filter_by(user.id)   
            if userservices is not None:
                db.session.delete(userservices)   
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
        try:
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
            return "Email verified"
        except:
            return "Invalid token"


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
                UserService.userid,
                Service.id,
                Service.name
            )
            .join(Service, UserService.serviceid == Service.id)
            .all()
        )

        response = [
        {
            "userid": r.userid,
            "serviceid": r.id,
            "servicename": r.servicename
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
                    Service.servicename
                )
                .join(Service, true())   # cross join
                .outerjoin(
                    UserService,
                    and_(
                        UserService.userid == User.id,
                        UserService.serviceid == Service.id
                    )
                )
                .filter(UserService.userid == None)
                .all()
            )

        response = [
            {
                "userid": r.userid,
                "serviceid": r.serviceid,
                "servicename": r.servicename
            }
            for r in results
        ]
        return response

    def services_add_all(services):
        for service in services:
            Utility.service_add(service["name"], service["desc"], service["url"], service["port"])
