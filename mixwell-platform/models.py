from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
import os
import smtplib
import socket
import sys
from flask import render_template, request
import psutil
import psycopg2
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy
import subprocess
import jwt # python -m pip install PyJWT
import subprocess

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)

from config.settings import Config

# ----------------------------
# 配置路径
# ----------------------------
PLATFORM_DIR = os.path.join(BASE_DIR, "MixwellSoftware.com-Services", "mixwell-platform") 
SERVICES_DIR = os.path.join(PLATFORM_DIR, "services")
PYTHON_PATH = os.path.join(PLATFORM_DIR, "venv", "Scripts", "python.exe")
ADMIN_DB = "postgres"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)

    services = db.relationship(
        "Service",
        secondary="users_services",   # 修正这里
        backref="users"
    )

class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    desc = db.Column(db.String(100), unique=False)
    url = db.Column(db.String(200), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20)) # running / stopped
    database = db.Column(db.String(100), unique=False)
    pid = db.Column(db.Integer, nullable=True)
    path = db.Column(db.String(200), nullable=False) 

class UserService(db.Model):
    __tablename__ = "users_services"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)    # 修正这里
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), primary_key=True)                 # 修正这里
    access = db.Column(db.Integer)


class Utility:

    ####################################
    # service methods
    ####################################

# service methods
    def services_get_all():
        return Service.query.all()

    def service_remove(servicename):
        try:
            service = Service.query.filter_by(name=servicename).first()
            Service.query.filter_by(id=service.id).delete()
            UserService.query.filter_by(service_id=service.id).delete()
            db.session.commit()
            return servicename
        except:
            return service
            
    def service_get(servicename):
        try:
            service = Service.query.filter_by(name=servicename).first()
            return service
        except:
            return service

    ####################################
    # users methods
    ####################################

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
            #login_user(user)
            return Utility.auth_response(200, "Login Scussfully!", user)

    def users_get_all():
        return User.query.all()

    def user_get(userid):                 
        user = User.query.get_or_404(userid)
        return user
                
    def user_remove(userid):
        UserService.query.filter_by(user_id=userid).delete()
        User.query.filter_by(id=userid).delete()
        db.session.commit()
        return userid

    def user_approve(userid):
        user = User.query.get_or_404(userid)
        user.is_verified = True
        db.session.commit()        
        return user

    def user_verify(token):
        user = Utility.user_bytoken(token)
        if user.is_verified == False:
            user.is_verified = True
            db.session.commit()
        return user            
    
    def user_verify_email(user_id, user_email):    
        token = Utility.user_token(user_id,  user_email, "")
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

    def user_token(userid, email, servicename):
        # Generate JWT token
        payload = {
            "userid": userid,
            "email": email,
            "servicename": servicename,
            "exp": datetime.now(timezone.utc) + timedelta(hours=12)
        }
        token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
        return token

    def user_check(servicename):
        token = request.cookies.get("access_token")
        if not token:
            return None
        try:
            decoded = jwt.decode(
                token,
                Config.JWT_SECRET,
                algorithms=["HS256"]
            )
            userid = decoded["userid"]
            user =  Utility.user_get(userid)            
            if user.is_admin:
                return user
            service = Service.query.filter_by(name=servicename).first()
            userservice = UserService.query.filter_by(   
                user_id=userid,
                service_id=service.id
            ).first()
            if not userservice:
                return None
            return user            
        except:
            return None
        


    def user_bytoken(token):
        decoded = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=["HS256"]
        )
        userid = decoded["userid"]
        user =  Utility.user_get(userid)
        return user

    def user_add_service_byname(userid, servicename): #update users_services table for connect user.id and service.id                
        if servicename & userid:
            service = Service.query.filter_by(name=servicename).first()                                
            userservice = Utility.user_add_service(userid, service.id)
            return userservice
        else:
            return None


    def user_add_service(userid, serviceid): #update users_services table for connect user.id and service.id        
        if not userid:
            return None
        if not serviceid:
            return None
        userservice = UserService.query.filter_by(   
            user_id=userid,
            service_id=serviceid
        ).first()

        if not userservice:
            userservice = UserService(
                user_id=userid,
                service_id=serviceid,
                access = 1
            )
            db.session.add(userservice)
            db.session.commit()
        return userservice

    def user_remove_service(userid, serviceid):  
        if not userid:
            return None
        if not serviceid:
            return None
        userService = UserService.query.filter_by(
            user_id=userid,
            service_id=serviceid
        ).first()
        db.session.delete(userService)
        db.session.commit()    
        return userService

    def user_with_services(user_id):
        userwithservices = (
            db.session.query(
                UserService.user_id,
                Service.id,
                Service.name,
                Service.url
            )
            .join(Service, UserService.service_id == Service.id)
            .filter(UserService.user_id == user_id)
            .all()
        )

        return userwithservices
    
    def users_list():

        rows = (
            db.session.query(
                User.id.label("user_id"),
                User.email,

                func.json_agg(
                    func.json_build_object(
                        "id", Service.id,
                        "name", Service.name
                    )
                ).filter(UserService.user_id == User.id).label("with_services"),

            )
            .select_from(User)
            .outerjoin(UserService, User.id == UserService.user_id)
            .outerjoin(Service, Service.id == UserService.service_id)
            .group_by(User.id)
            .order_by(User.id)
            .all()
        )

        # all services once
        all_services = db.session.query(Service.id, Service.name).all()

        users = []

        for r in rows:

            with_services = r.with_services or []

            with_ids = {s["id"] for s in with_services}

            without_services = [
                {"id": s.id, "name": s.name}
                for s in all_services
                if s.id not in with_ids
            ]

            users.append({
                "user_id": r.user_id,
                "email": r.email,
                "service_count": len(with_services),
                "with_services": with_services,
                "without_services": without_services
            })

        return users

    def auth_response(status, message, data):
        return {"status" : status, "message" : message, "data" : data}

    ####################################
    # admin methods
    ####################################

#    from your_auth_model import db, Service  # 替换成你实际 DB model
    from datetime import datetime

    # ----------------------------
    # 工具函数
    # ----------------------------

    def generate_service_scripts(service_name, port, service_path, python_path):
        """为 service 生成 start/stop bat 文件"""
        start_bat = os.path.join(service_path, f"{service_name}_start.bat")
        stop_bat = os.path.join(service_path, f"{service_name}_stop.bat")

        start_content = f"""@echo off
            cd /d %~dp0
            REM Start {service_name} on port {port}
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :{port}') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" cmd /c "{python_path} {os.path.join(service_path, 'app.py')} {port} >> {os.path.join(service_path, 'service.log')} 2>&1"
            echo {service_name} started on port {port}
            """

        stop_content = f"""@echo off
            cd /d %~dp0
            REM Stop {service_name} on port {port}
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :{port}') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo {service_name} stopped
            """

        with open(start_bat, "w", encoding="utf-8") as f:
            f.write(start_content)
        with open(stop_bat, "w", encoding="utf-8") as f:
            f.write(stop_content)

    def init_service_db(service_path):
        try:
            """初始化 service 数据库 (可自定义每个 service 的 db 脚本)"""
            init_file = os.path.join(service_path, "init_db.py")
            if os.path.exists(init_file):
                subprocess.run([PYTHON_PATH, init_file])
        except:
            return None
        
    def services_register(SERVICES_PATH, base_port):
        try:
            folder_list = os.listdir(SERVICES_PATH)        
            port = base_port            
            for folder in folder_list:

                service_path = os.path.join(SERVICES_PATH, folder).lower()

                if not os.path.isdir(service_path):
                    continue

                # split folder name
                #parts = folder.split("_", 1)

                #if len(parts) != 2:
                #    print(f"Invalid service folder name: {folder}")
                #    continue

                #port = int(parts[0])
                #if port < base_port : # base_port would be 5000 or 8000 
                #    port = base_port + port - 5000
                port = port + 1
                name = folder                
                path = service_path
                url = f"{Config.GATEWAY_URL}:{port}"

                # 初始化数据库
                dbname = f"{name}_{port}"
                Utility.create_service_database(dbname)
                print(f"DB created for {dbname}")

                # Start Service
                prodc = Utility.service_start(name, port, service_path)                
                pid = None
                if prodc:
                    pid = prodc.pid
                    status = "running"
                else:
                    status = "stopped"
                service = Service.query.filter_by(name=name).first()
                if not service:
                    # 新服务
                    service = Service(
                        name=name,                                
                        desc = f"{name} serv",
                        database = dbname,
                        port=port,
                        url=url,
                        path=path,
                        pid = pid,                        
                        status = status
                    )
                    db.session.add(service)
                    db.session.commit()
                    print(f"New service detected: {folder}")


                    # 生成 start/stop 脚本
                    #Utility.generate_service_scripts(folder, port, service_path, PYTHON_PATH)
                    #print(f"Start/stop scripts generated for {service.name}")

                else:
                    service.database = dbname,
                    service.port=port,
                    service.url=url,
                    service.path=path,
                    service.pid = pid,                        
                    service.status = status
                    db.session.commit()
                    print(f"Service {folder} updated")
    
            db_services = {s.name: s for s in Service.query.all()}
            # 删除已不存在的 service
            current_set = set(folder_list)
            for name, service in db_services.items():
                searchname = f"{service.port}_{service.name}" 
                if searchname not in current_set:
                    #Utility.service_stop(service.name)
                    db.session.delete(service)
                    db.session.commit()
                    Utility.drop_service_database(service["database"])
                    print(f"Removed service {name} from DB")
        except:
            return None

    import psycopg2    
    from sqlalchemy import create_engine


    def create_service_database(db_name):
        
        try:
            #db_name = service_name
            conn = psycopg2.connect(
                dbname=ADMIN_DB,
                user=ADMIN_DB,
                password=Config.SQLALCHEMY_DATABASE_KEY,
                host="localhost",
                port="5432"
            )

            conn.autocommit = True
            cur = conn.cursor()

            cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
            exists = cur.fetchone()

            if not exists:
                cur.execute(f'CREATE DATABASE "{db_name}"')
                print(f"Database created: {db_name}")

            cur.close()
            conn.close()


            #DB_USER = ADMIN_DB
            #DB_PASSWORD = ADMIN_DB
            #DB_HOST = "localhost"
            #DB_PORT = "5432"

            #DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"

            #engine = create_engine(DATABASE_URL)

            return db_name
        except psycopg2.Error as e:
            print("PG ERROR", e)
            print("PG pgerror", e.pgerror)
            print("PG pgcode", e.pgcode)
            return None
    
    def drop_service_database(db_name):
        try:
            conn = psycopg2.connect(
                dbname=ADMIN_DB,
                user=ADMIN_DB,
                password=Config.SQLALCHEMY_DATABASE_KEY,
                host="localhost"
            )

            conn.autocommit = True
            cur = conn.cursor()

            # terminate existing connections
            cur.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}'
                AND pid <> pg_backend_pid();
            """)

            # drop database
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')

            print(f"Database dropped: {db_name}")

            cur.close()
            conn.close()        
            return True
        except:
            return False
    
    def is_port_open(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(("127.0.0.1", port)) == 0
        except:
            return False

    def service_start1(servicename, port, servicepath):
        try:
            service = Service.query.filter_by(name=servicename).first()

            if service:
                Utility.service_stop(servicename)

            app_file = os.path.join(servicepath, "app.py")

            base_db_url = Config.SQLALCHEMY_DATABASE_URI.rsplit("/", 1)[0]
            app_db = f"{base_db_url}/{servicename}_{port}"
            
            """
            # 🔥 构造 DB URL
            base_db_url = Config.SQLALCHEMY_DATABASE_URI.rsplit("/", 1)[0]
            db_name = f"{servicename}_{port}"
            app_db = f"{base_db_url}/{db_name}"

            base = Config.SQLALCHEMY_DATABASE_URI.rsplit("/", 1)[0]
            db_name = f"{servicename}_{port}"
            servicedb = f"{base}/{db_name}"            
            """

            if os.path.exists(app_file):
                proc = subprocess.Popen(
                    [
                        PYTHON_PATH,
                        app_file,
                        str(port),
                        app_db
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return proc

        except Exception as e:
            print("Service start error:", e)
            return None

    def service_start(servicename, port, servicepath):
        proc = None
        try:
            service = Service.query.filter_by(name=servicename).first()
            if service:
                #port = Utility.is_port_open(service.port)
                #if port:                
                Utility.service_stop(servicename)            
            app_file = os.path.join(servicepath, f"app.py")
            app_db = f"{Config.SQLALCHEMY_DATABASE_URI}/{servicename}_{port}"
            if os.path.exists(app_file):                            
                proc = subprocess.Popen([
                        PYTHON_PATH,
                        app_file,
                        str(port),
                        app_db]                    
#                    [PYTHON_PATH, f"{app_file} {service.port} {app_db}"
                    
                    ,creationflags=subprocess.CREATE_NO_WINDOW
                )            
        except:
            return None
        return proc                
    
    def service_stop(servicename):
            service = Service.query.filter_by(name=servicename).first()
            try:
                if service.pid:
                    p = psutil.Process(service.pid)
                    p.kill()
                    #p.terminate()  # 或 p.kill() 强制杀掉
                    #p.wait(timeout=5)
            except Exception as e:
                print(e)
            service.status = "stopped"
            service.pid = None
            db.session.commit()
            return service


    def service_view(service_id):
        try:        
            service = Utility.service_get(service_id)
            if service:            
                if Utility.is_port_open(service.id):
                    return service
                else:
                    print("Service is NOT running ❌")        
                    return None                
            else:
                print("Service is NOT running ❌")        
                return None
        except:
            return False    