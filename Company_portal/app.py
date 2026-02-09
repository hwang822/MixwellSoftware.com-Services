from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, LoginLog, ChatMessage

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- AUTO CREATE ADMIN ----------
def create_admin():
    if User.query.count() == 0:
        admin = User(
            username="admin",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin: admin / admin123")


# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        user = User.query.filter_by(
            username=request.form["username"]
        ).first()

        if user and check_password_hash(
                user.password,
                request.form["password"]
        ):
            login_user(user)

            db.session.add(LoginLog(user_id=user.id))
            db.session.commit()

            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":

        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"])
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")

@app.route("/service")
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

@app.route("/dashboard")
@login_required
def dashboard():
    services = [
        {"name": "AI Service", "url": "http://localhost:8000"},
        {"name": "Video Service", "url": "http://localhost:8000"},
        {"name": "Data API", "url": "http://localhost:8000"},
        {"name": "Travel", "url": "http://localhost:8000"},
        {"name": "Cam", "url": "http://localhost:8000"},
        {"name": "Rdp", "url": "http://localhost"},
        {"name": "Email", "url": "http://localhost:8000"}

    ]
    return render_template("dashboard.html", services=services)

@app.route("/service/<name>")
@login_required
def service(name):
    return render_template("service.html", service=name)


@app.route("/logout")
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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()

    socketio.run(app, debug=True)
