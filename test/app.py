from flask import Flask
from Services.LoginService.loginService import loginService

app = Flask(__name__)

app.register_blueprint(loginService, url_prefix="/login")

if __name__ == "__main__":
    app.run(debug=True, port="5001")  # Test app port 5001