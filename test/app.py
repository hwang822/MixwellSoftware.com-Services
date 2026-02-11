from flask import Flask
from Services.LoginService.loginService import login_bp

app = Flask(__name__)

app.register_blueprint(login_bp, url_prefix="/login")

if __name__ == "__main__":
    app.run(debug=True)