from flask import Flask, request, jsonify, render_template
from models import db, User, Service, UserService
from config import Config
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from email_service import send_verify_email
from sqlalchemy.engine import URL
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

#JWT_SECRET = "your_secret_key_here"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------
# SIGNUP
# -------------------------
@app.route("/user/signup", methods=["GET", "POST"])
def user_signup():
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form["username"]
    password = generate_password_hash(request.form["password"])    

    user = User(email=email, 
        password=password, 
        is_verified=False, 
        created_at = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())
    )
    db.session.add(user)
    db.session.commit()
    
    send_verify_email(user.id, email)

# -------------------------
# VERIFY EMAIL
# -------------------------

@app.route("/user/verify/<token>")
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

# -------------------------
# LOGIN
# -------------------------
@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "GET":
        return render_template("login.html")

#    data = request.json
    email = request.form["username"]
    password = request.form["password"]    
    user = User.query.filter_by(email=email).first()

    if user is None:
        return render_template("signup.html")
        #return {"message": "Invalid username!"}, 401
    elif not check_password_hash(
        user.password, 
        password):
        return {"message": "Invalid password!"}, 401
    elif user.is_verified == False:
        return {"message": "verify email for approved."}, 200
    else:
        #login_user(user)
        # Generate JWT token for email verification
        send_verify_email(user.id, user.email)
        return {"message": "login successful!"}, 200

def create_admin():
    if User.query.count() == 0:
        admin = User(            
            email="admin",
            password=generate_password_hash("admin123"),
            is_verified = True,
            is_admin = True,
            created_at = datetime.now(timezone.utc) + timedelta(hours=12)  # can not datetime.utcnow())
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin: admin / admin123")
# -------------------------
# USER DELETE
# -------------------------
@app.route("/user/delete/<int:userid>", methods=["GET", "POST"])
def user_delete(userid):
    user = User.query.get_or_404(userid)
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "user (user_id:{userid} has been deleteed"})

@app.route("/user/approve/<int:userid>")
@login_required
def approve_user(userid):
    if not current_user.is_admin:
        return "Access denied", 403
    user = User.query.get(userid)
    user.is_approved = True
    db.session.commit()
    return

@app.route("/user/remove_service_from_user/<int:user_id>", methods=["POST"])
@login_required
def admin_remove_service_from_user(user_id):  
    results = (
        db.session.query(User, UserService)
        .join(UserService, UserService.userid == user_id)        
        .all()
    )

    service_id = request.form.get("service_id")

    userServices = UserService.query.filter_by(
        userid=user_id,
        serviceid=service_id
    ).all()

    for userService in userServices:        
        db.session.delete(userService)
        db.session.commit()    
    return 


# -------------------------
# SERVICE 
# -------------------------

def service_register(user_id, service_name):

    # Get or create Service
    
    service = Service.query.filter_by(name=service_name).first()
    if not service:
        service = Service(
                name=service_name,
                desc = service_name,
                token = "",
                url = "",
                port = 0                        
            )
        db.session.add(service)
        db.session.flush()   # get service.id without commit

    # Get or create UserService
    userservice = UserService.query.filter_by(
        user_id=user_id,
        service_id=service.id
    ).first()

    if not userservice:
        userservice = UserService(
            user_id=user_id,
            service_id=service.id,
            access = 1
        )
        db.session.add(userservice)

    db.session.commit()

    return userservice

@app.route("/service/all", methods=["GET", "POST"])
def service_all():
    return Service.query.all()

@app.route("/service/user_with_services")
def user_services():
    return Service.query.all()

@app.route("/service/delete/<int:service_id>", methods=["GET", "POST"])
def service_delete(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()

    return Service.query.all()

@app.route("/service/user_without_services")
def user_without_services():
    return Service.query.all()

@app.route("/service/user_with_services")
def user_with_services():
    return Service.query.all()

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
        create_admin()
        service_register(5, "service1")
    app.run(port=5003)

