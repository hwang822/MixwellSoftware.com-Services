from flask import Flask, request, jsonify, render_template
from models import db, User
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from email_service import send_verify_email
from sqlalchemy.engine import URL
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# -------------------------
# SIGNUP
# -------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form["username"]
    password = request.form["password"]    

    user = User(email=email, 
        password=password, 
        is_verified=False, 
        created_at = datetime.utcnow())

    db.session.add(user)
    db.session.commit()

    send_verify_email(user)

    return jsonify({"message": "Check your email"})


# -------------------------
# VERIFY EMAIL
# -------------------------
@app.route("/verify/<token>")
def verify(token):
    try:
        email = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])["email"]
        user = User.query.filter_by(email=email).first()
        user.is_verified = True
        db.session.commit()
        return "Email verified"
    except:
        return "Invalid token"


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

#    data = request.json
    email = request.form["username"]
    password = request.form["password"]    
    user = User.query.filter_by(email=email).first()

    #if not user or not check_password_hash(user.password, password):
    if not user or not user.password == password:
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.is_verified:
        return jsonify({"error": "Email not verified"}), 403

    payload = {
        "user_id": 1,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }

    token = jwt.encode(payload, "your_secret_key", algorithm="HS256")


    return jsonify({"token": token})


# -------------------------
# VERIFY TOKEN API
# -------------------------
@app.route("/api/verify_token")
def verify_token():
    token = request.headers.get("Authorization")
    try:
        data = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        return jsonify({"user_id": data["user_id"]})
    except:
        return jsonify({"error": "Invalid"}), 401


if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=5003)