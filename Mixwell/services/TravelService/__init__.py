from flask import Flask
from travelService import travelService

app = Flask(__name__)

app.register_blueprint(travelService, url_prefix="/ai")

if __name__ == "__main__":
    app.run(debug=True, port="5005")