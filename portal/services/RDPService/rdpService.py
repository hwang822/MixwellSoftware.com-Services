from flask import Flask, Blueprint, render_template

rdpService = Blueprint("rdpService", __name__)

@rdpService.route("/")
def rdp_home():
    return render_template("RDPService.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(rdpService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5007) 