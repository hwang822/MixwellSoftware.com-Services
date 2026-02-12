from flask import Flask, Blueprint, render_template

dataAPIService = Blueprint("dataAPIService", __name__)

@dataAPIService.route("/")
def dataAPI_home():
    return render_template("DataAPIService.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(dataAPIService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5006)  # localhost only