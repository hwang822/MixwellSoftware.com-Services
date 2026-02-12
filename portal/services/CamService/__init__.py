import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flask import Flask
from services.CamService.camService import camService
app = Flask(__name__)

app.register_blueprint(camService, url_prefix="/cam")

if __name__ == "__main__":
    app.run(debug=True, port="5002")  # Test app port 5001