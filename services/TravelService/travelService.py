from flask import Flask, Blueprint, render_template

travelService = Blueprint("travelService", __name__)

@travelService.route("/")
def travel_home():
    return render_template("TravelService.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(travelService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5005)