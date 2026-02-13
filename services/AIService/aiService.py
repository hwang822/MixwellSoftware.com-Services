import os
import sys
from flask import Flask, Blueprint, render_template
BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')

aiService = Blueprint("aiService", __name__)

@aiService.route("/")
def ai_home():
    return render_template("AIService.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(aiService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=BASE_PORT)