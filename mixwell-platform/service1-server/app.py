import os
import sys

from flask import Flask, render_template, request, redirect
from models import db
from flask import request, redirect, render_template
import jwt

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from config.settings import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


@app.route("/")
def home():

    token = request.cookies.get("access_token")
    if not token:
        return redirect("http://localhost:5003/user/signup")

    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return redirect("http://localhost:5003/user/login")
    except jwt.InvalidTokenError:
        return redirect("http://localhost:5003/user/login")

    return render_template("service1.html")

"""
def home():
    token = request.cookies.get("jwt")
    
    response = []

    if not token:
        response = redirect("http://localhost:5003/user/signup")
        return response
    
    r = requests.get(AUTH_URL, headers={"Authorization": token})
    if r.status_code != 200:
        return redirect("http://localhost:5003/user/login")

    return render_template("service1.html")
"""
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=5001)