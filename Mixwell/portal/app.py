import os
import sys
import jwt
from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_socketio import SocketIO, emit
from sqlalchemy import and_, true
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, Users, ChatMessage, Services, UsersServices
import uuid
from flask import send_from_directory

app = Flask(__name__)
app.config.from_object(Config)
BASE_PORT = app.config['PORT']
BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///app_{BASE_PORT}.db"
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')
db.init_app(app)
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# portal/api.py
import datetime
from flask import Blueprint, request

api = Blueprint("api", __name__)

# Flask session secret
app.config["SECRET_KEY"] = "service-session-secret"

# JWT secret (must match portal if verifying across apps)
JWT_SECRET = "jwt-signing-secret"


# ---------- Login, siginup, logout ROUTES ----------

@app.route("/")
def home():
    services = Services.query.all()
    return render_template("home.html", services=services)    

@app.route("/signup/", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        session.pop('_flashes', None)
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])    
        response = user_signup(username, password)
        message = response[0]['message']
        error = response[1]        
        flash(message)
        if error == 200:            
            return redirect("/login")
    return render_template("signup.html")

@app.route("/login/", methods=["GET","POST"])
def login():
    if request.method == "POST":        
        session.pop('_flashes', None)
        username = request.form["username"]
        password = request.form["password"]    
        response = user_login(username, password)
        message = response[0]['message']
        error = response[1]        
        flash(message)
        if error == 200:            
            if current_user.is_admin:
                return render_template("admin_dashboard.html")
            else:
                return render_template("user_dashboard.html")                    
    return render_template("login.html")
        
@app.route("/logout/")
def logout():
    logout_user()
    return redirect("/")    

# ---------- API ROUTES ----------

@app.route("/api/serviceregister/", methods=["GET","POST"])
def api_service_register():   # http://localhost:5000/api/signup    
    data = request.get_json()
    servicename = data["servicename"]
    servicedesc = data["servicedesc"]
    url = data["url"]
    port = data["port"]        
    service = Services(servicename=servicename, 
                     servicedesc=servicedesc, 
                     url=url,
                     port=port 
    )

    response = add_service(service)
    return response    

@app.route("/api/usersignup/", methods=["GET","POST"])
def api_user_signup():   # http://localhost:5000/api/signup
    data = request.get_json()
    lgoinUN = data["username"]
    lgoinPS = data["password"]
    lgoinPSHash = generate_password_hash(lgoinPS) 
    new_user = Users(username=lgoinUN, 
                     password=lgoinPSHash, 
                     is_approved=True, 
                     is_admin=False)
    try:
        db.session.add(new_user)
        db.session.commit()
        #flash("Signup successful! Waiting for admin approval.")
    except:
        db.session.rollback()
        #flash("Username already exists.")
        return {"error": "Username already exists."}, 401
    return {"error": "Signup successful!"}, 200

@app.route("/api/userlogin/", methods=["GET","POST"])
def api_user_login(): #http://localhost:5000/api/login
    data = request.get_json()
    lgoinUN = data["username"]
    lgoinPS = data["password"]
    servicename = data["servicename"]
    response = user_login(lgoinUN, lgoinPS)
    error = response[1]        
    if error != 200:
        return {
            "token": None
        }, 401
    api_add_service_to_user(current_user.id, servicename)        
    payload = {
        "user_id": current_user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return {
        "token": token
    }, 200


@app.route("/api/userverify/", methods=["GET","POST"])
def api_user_verify_token():
    try:
        data = request.get_json()
        decoded = jwt.decode(
            data["token"],
            JWT_SECRET,
            algorithms=["HS256"]
        )
        return {"valid": True, "user_id": decoded["user_id"]}, 200
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}, 401
# ---------- service ROUTES ----------


@app.route("/service/")
@login_required
def service_page():
    from flask import request
    service_name = request.args.get("name")
    service_url = request.args.get("url")
    return render_template(
        "service.html",
        service=service_name,
        service_url=service_url
    )

@app.route("/service/<name>/")
@login_required
def service(name):
    return render_template("user_service.hml", service=name)

# ===============================
#  Dashboard ROUTE
# ===============================


@app.route("/dashboard/")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect('/admin_dashboard')
    else:
        return redirect('/user_dashboard')
        
@app.route("/user_dashboard/")
@login_required
def user_dashboard():    
    if UsersServices.query.count() > 0:         
        results = (
            db.session.query(
                UsersServices.userid,
                Services.servicename,
            )
            .join(
                Services,
                and_(
                    UsersServices.userid == current_user.id,
                    UsersServices.serviceid == Services.id
                )
            )
            .all()
        )    
        
        services = [
            {
                "userid": r.userid,
                "servicename": r.servicename
            }
            for r in results
        ]
        db.session.query()
    return render_template("user_dashboard.html", services=services)

@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return "Access denied", 403
    return render_template("admin_dashboard.html")

# ===============================
# admin Services Management``
# ===============================

@app.route("/admin/services")
@login_required
def admin_services():
    if not current_user.is_admin:
        return "Access denied", 403
    services = Services.query.all()
    return render_template("admin_services.html", services=services)

def add_service(service):    
    try:
        current_time = datetime.datetime.now() 
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        service.starttime = formatted_time    
        service.token=str(uuid.uuid4())
        if Services.query.count() > 0:
            serviceexit = Services.query.filter_by(servicename=service.servicename).first()        
            if serviceexit is not None:
                service = serviceexit
        db.session.add(service)
        db.session.commit()
    except:
        return {"message": "service register no successful!"}, 401    
    return {"message": "service register successful!"}, 200

@app.route("/admin/services/admin_add_service", methods=["POST"])
@login_required
def admin_add_service():    
    service = Services(
        servicename=request.form["servicename"],
        url=request.form["url"],
        port=request.form["port"],
        servicedesc=request.form["servicedesc"]                    
    )
    response = add_service(service)
    if response[1] == 200:
        return redirect(url_for("admin_services"))
    return 

@app.route("/admin/services/admin_delete_service/<int:serviceid>")
@login_required
def admin_delete_service(serviceid):
    service = Services.query.get_or_404(serviceid)
    db.session.delete(service)    
    db.session.commit()
    return redirect(url_for("admin_services"))

@app.route("/admin/services/admin_start_service/<int:serviceid>")
@login_required
def admin_start_service(serviceid):
    service = Services.query.get_or_404(serviceid)
    url = service.url
    return redirect(url)

# ===============================
# admin Users Management
# ===============================
def user_login(username, password):
    session.pop('_flashes', None)
    user = Users.query.filter_by(            
        username=username
    ).first()

    if user is None:
        return {"message": "Invalid username!"}, 401
    elif not check_password_hash(
        user.password, 
        password):
        return {"message": "Invalid password!"}, 401
    elif user.is_approved == False:
        return {"message": "Your account is not approved yet."}, 200
    else:
        login_user(user)
        return {"message": "Signup successful!"}, 200
        
def user_signup(username, password):
    if request.method == "POST":    
        session.pop('_flashes', None)
        password = generate_password_hash(password)    
        # 创建用户，但默认未批准
        new_user = Users(username=username, password=password, is_approved=True, is_admin=False)
        try:
            db.session.add(new_user)
            db.session.commit()
            return {"message": "Signup successful!, wait email approve!"}, 200
        except:
            db.session.rollback()
            return {"message": "Username already exists!"}, 401        
    return render_template("signup.html")

def get_userswithservices():
    results = []
    results = (        
        db.session.query(
                UsersServices.userid,
                Services.id,
                Services.servicename
            )
            .join(Services, UsersServices.serviceid == Services.id)
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

def get_userswithoutservices():

    results = []
    if UsersServices.query.count()>0:
        results = (
            db.session.query(
                Users.id.label("userid"),
                Services.id.label("serviceid"),
                Services.servicename
            )
            .join(Services, true())   # cross join
            .outerjoin(
                UsersServices,
                and_(
                    UsersServices.userid == Users.id,
                    UsersServices.serviceid == Services.id
                )
            )
            .filter(UsersServices.userid == None)
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

@app.route("/admin/users")
@login_required
def admin_users():
    users = Users.query.all()
    services = Services.query.all()
    userswithservices = get_userswithservices()
    userswithoutservices = get_userswithoutservices()
    return render_template("admin_users.html", users=users, 
                           services=services, 
                           userswithservices = userswithservices, 
                           userswithoutservices=userswithoutservices)

@app.route("/admin/users/admin_approve_user/<int:userid>")
@login_required
def admin_approve_user(userid):
    if not current_user.is_admin:
        return "Access denied", 403

    user = Users.query.get(userid)
    user.is_approved = True
    db.session.commit()
    return redirect("/admin/users")

#🔹 删除 Service（自动清理 userservice）
@app.route("/admin/users/admin_delete_user/<int:userid>")
@login_required
def admin_delete_user(userid):
    user = Users.query.get_or_404(userid)
    db.session.delete(user)
    db.session.commit()

    return redirect("/admin/users")

def api_add_service_to_user(user_id, servicname):
    if Services.query.count() > 0:
        service = Services.query.filter_by(servicename=servicname).first()        
        if service is not None:
            userService = UsersServices(
                userid = user_id,
                serviceid = service.id
            )
            db.session.add(userService)
            db.session.commit() 
    return            

@app.route("/admin/users/admin_add_service_to_user/<int:user_id>", methods=["POST"])
@login_required
def admin_add_service_to_user(user_id):
    service_id = request.form.get("service_id")
    userService = UsersServices(
        userid = user_id,
        serviceid = service_id
    )
    db.session.add(userService)
    db.session.commit()    
    return redirect(url_for("admin_users"))

@app.route("/admin/users/admin_remove_service_from_user/<int:user_id>", methods=["POST"])
@login_required
def admin_remove_service_from_user(user_id):  
    results = (
        db.session.query(Users, UsersServices)
        .join(UsersServices, Users.id == Users.userid)        
        .all()
    )

    service_id = request.form.get("service_id")

    userServices = UsersServices.query.filter_by(
        userid=user_id,
        serviceid=service_id
    ).all()

    for userService in userServices:        
        db.session.delete(userService)
        db.session.commit()    
    return redirect(url_for("admin_users"))

# ---------- app ROUTE ----------

@app.route("/downloads/<filename>")
def download_file(filename):
    download_folder = os.path.join(app.root_path, "downloads")
    return send_from_directory(download_folder, filename, as_attachment=True)

@app.route("/services/service_download/<int:serviceid>", methods=["GET","POST"])
def service_download(serviceid):
    serviceGet = Services.query.get_or_404(serviceid)

    service = {
        "name": serviceGet.servicename,
        "url": url_for("download_file", filename=f"{serviceGet.servicename}App.exe"),
        "android_url": "#",
        "ios_url": "#"
    }    
    return render_template("serviceapp_download.html",service=service)


# ---------- AUTO CREATE ADMIN ----------
def create_admin():
    if Users.query.count() == 0:
        admin = Users(            
            username="admin",
            password=generate_password_hash("admin123"),
            is_approved = True,
            is_admin = True
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin: admin / admin123")

# ---------- AUTO CREATE Seed Service ----------

def create_seed_service():
    try:
        if Services.query.count() == 0:
            services = [
                {"servicename": "AIService", "servicedesc": "AI Service", "url": f"http://127.0.0.1", "port": f"{BASE_PORT+1}"},
                {"servicename": "CamService", "servicedesc": "Cam Service", "url": f"http://127.0.0.1", "port": f"{BASE_PORT+2}"},
                {"servicename": "VideoService", "servicedesc": "Video Service", "url": f"http://127.0.0.1", "port": f"{BASE_PORT+3}"},
                {"servicename": "EmailService", "servicedesc": "Email Service", "url": f"http://127.0.0.1", "port": f"{BASE_PORT+4}"},
                {"servicename": "TravelService", "servicedesc": "Travel Service", "url": f"http://127.0.0.1", "port": f"{BASE_PORT+5}"},
                {"servicename": "DataAPIService", "servicedesc": "Data Service", "url": f"http://127.0.0.1", "port": f"{BASE_PORT+6}"},
                {"servicename": "RdpService", "servicedesc": "RDP Service", "url": f"http://127.0.0.1", "port": f"{BASE_PORT+7}"}
            ]        
            port = BASE_PORT
            for service in services:
                port = port + 1
                service = Services(
                    servicename=service['servicename'],
                    url=service['url'],
                    port=port,
                    servicedesc=service['servicedesc']
                )
                add_service(service)
            print("Created seed services")
    except:
        print("failure to create seed services")
# ---------- CHAT ----------
@socketio.on("send_message")
def handle_message(data):
    db.session.add(ChatMessage(
        username=data["user"],
        message=data["msg"]
    ))
    db.session.commit()

    emit("receive_message", data, broadcast=True)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()
        create_seed_service()

    socketio.run(app, debug=False, port=BASE_PORT)
