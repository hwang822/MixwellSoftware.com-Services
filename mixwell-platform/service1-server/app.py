from flask import Flask, request, redirect
from models import db
from config import Config
import requests

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

AUTH_URL = "http://localhost:5003/api/verify_token"

@app.route("/")
def home():
    token = request.cookies.get("jwt")
    if not token:
        return redirect("http://localhost:5003/login")

    r = requests.get(AUTH_URL, headers={"Authorization": token})
    if r.status_code != 200:
        return redirect("http://localhost:5003/login")

    return "Welcome to Service1"

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    app.run(port=5001)