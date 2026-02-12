from flask import Flask, Blueprint

camService = Blueprint("camService", __name__)

@camService.route("/")
def cam_home():
    return "Cam Service: Internal Only"

def create_app():
    app = Flask(__name__)
    app.register_blueprint(camService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5002)