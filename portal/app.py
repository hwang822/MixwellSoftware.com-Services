import os
import sys
from flask import Flask, abort, flash, render_template, render_template_string, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
import requests
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, Users, ChatMessage, Services, UserServices

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
# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("home.html", services=[])    

@app.route("/login/", methods=["GET","POST"])
def login():
    if request.method == "POST":

        user = Users.query.filter_by(
            username=request.form["username"]
        ).first()

        if user is None:
            flash("Invalid username")
        elif not check_password_hash(
            user.password, 
            request.form["password"]):
            flash("Invalid password")
        elif user.is_approved == False:
            flash("Your account is not approved yet. Please wait for admin approval.")
        else:
            login_user(user)
            flash("Login successful!")
            if current_user.is_admin:
                return redirect('/admin_dashboard')
            else:
                return redirect('/user_dashboard')
    return render_template('login.html')
@app.route("/signup/", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])    
        # 创建用户，但默认未批准
        new_user = Users(username=username, password=password, is_approved=False, is_admin=False)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Signup successful! Waiting for admin approval.")
        except:
            db.session.rollback()
            flash("Username already exists.")
        return redirect("/login")
    return render_template("signup.html")
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

    services = [
        {"name": "AI Service", "url": f"http://127.0.0.1:{BASE_PORT+1}/"},
        {"name": "Cam Service", "url": f"http://127.0.0.1:{BASE_PORT+2}/"},
        {"name": "Video Service", "url": f"http://127.0.0.1:{BASE_PORT+3}/"},
        {"name": "Email Service", "url": f"http://127.0.0.1:{BASE_PORT+4}/"},
        {"name": "Travel Service", "url": f"http://127.0.0.1:{BASE_PORT+5}/"},
        {"name": "Data API Service", "url": f"http://127.0.0.1:{BASE_PORT+6}/"},
        {"name": "Rdp Service", "url": f"http://127.0.0.1:{BASE_PORT+7}/"}
   
    ]    
    if current_user.is_admin:
        services.append({"name": "Admin", "url": url_for("admin_service", _external=True)})
        services.append({"name": "App Registery Service", "url": url_for("registery_service", _external=True)})

    return render_template("dashboard.html", services=services)

@app.route("/service/<name>/")
@login_required
def service(name):
    return render_template("service.hml", service=name)


@app.route("/logout/")
def logout():
    logout_user()
    return redirect("/")


# ---------- CHAT ----------
@socketio.on("send_message")
def handle_message(data):
    db.session.add(ChatMessage(
        username=data["user"],
        message=data["msg"]
    ))
    db.session.commit()

    emit("receive_message", data, broadcast=True)


# ===============================
# Admin Dashboard
# ===============================

@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return "Access denied", 403
    return render_template("admin_dashboard.html")

# ===============================
# Services Management
# ===============================

@app.route("/admin/services")
@login_required
def admin_services():
    if not current_user.is_admin:
        return "Access denied", 403
    services = Services.query.all()
    return render_template("admin_services.html", services=services)

@app.route("/admin/services/admin_add_service", methods=["POST"])
@login_required
def admin_add_service():
    new_service = Services(
        servicename=request.form["servicename"],
        token=str(uuid.uuid4()),
        url=request.form["url"],
        port=request.form["port"]
    )
    db.session.add(new_service)
    db.session.commit()
    return redirect(url_for("admin_services"))

@app.route("/admin/services/admin_delete_service2")
@login_required
def admin_delete_service2():
    return redirect(url_for("admin_services"))

@app.route("/admin/services/admin_delete_service/<int:serviceid>")
@login_required
def admin_delete_service(serviceid):
    service = Services.query.get_or_404(serviceid)
    db.session.delete(service)    
    db.session.commit()
    return redirect(url_for("admin_services"))

# ===============================
# Users Management
# ===============================

@app.route("/admin/users")
@login_required
def admin_users():
    users = Users.query.all()
    services = Services.query.all()
    return render_template("admin_users.html", users=users, services=services)

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

@app.route("/admin/users/admin_add_service_to_user/<int:user_id>", methods=["POST"])
#@login_required
def admin_add_service_to_user(user_id):
    service_id = request.form.get("service_id")
    userService = UserServices(
        userid = user_id,
        serviceid = service_id
    )
    db.session.add(userService)
    db.session.commit()    
    return redirect(url_for("admin_users"))

@app.route("/admin/users/admin_remove_service_from_user/<int:user_id>", methods=["POST"])
#@login_required
def admin_remove_service_from_user(user_id):  
    service_id = request.form.get("service_id")

    userServices = UserServices.query.filter_by(
        userid=user_id,
        serviceid=service_id
    ).all()

    for userService in userServices:        
        db.session.delete(userService)
        db.session.commit()    
    return redirect(url_for("admin_users"))

#🔹 新增 Service
import uuid


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()

    socketio.run(app, debug=False, port=BASE_PORT)
