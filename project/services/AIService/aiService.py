from flask import Flask, Blueprint

aiService = Blueprint("aiService", __name__)

@aiService.route("/")
def ai_home():
    return "AI Service: Internal Only"

def create_app():
    app = Flask(__name__)
    app.register_blueprint(aiService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5001)  # localhost only