from flask import Flask, Blueprint
import flask, flask_login, flask_sqlalchemy, flask_socketio
import cv2
import requests
import kivy

app = Flask(__name__)
bp = Blueprint("test", __name__)

@app.route("/")
def home():
    return "Flask OK"

if __name__ == "__main__":
    app.run(port=8080)