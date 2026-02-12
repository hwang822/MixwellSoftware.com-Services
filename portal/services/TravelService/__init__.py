import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flask import Flask
from services.TravelService.travelService import travelService

app = Flask(__name__)

app.register_blueprint(travelService, url_prefix="/ai")

if __name__ == "__main__":
    app.run(debug=True, port="5005")  # Test app port 5005