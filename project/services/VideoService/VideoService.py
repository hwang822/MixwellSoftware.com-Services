from flask import Flask, Blueprint

videoService = Blueprint("videoService", __name__)

@videoService.route("/")
def video_home():
    return "Video Service: Internal Only"

def create_app():
    app = Flask(__name__)
    app.register_blueprint(videoService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5003)