from flask import Flask, Blueprint, render_template
import os
import sys
from flask import Flask, Blueprint
BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5006
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')

dataAPIService = Blueprint("dataAPIService", __name__)

@dataAPIService.route("/")
def dataAPI_home():
    return render_template("DataAPIService.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(dataAPIService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=BASE_PORT)  # localhost only