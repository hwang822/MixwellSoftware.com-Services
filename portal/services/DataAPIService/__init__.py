import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flask import Flask
from services.DataAPIService.dataAPIService import dataAPIService
app = Flask(__name__)

app.register_blueprint(dataAPIService, url_prefix="/dataAPI")

if __name__ == "__main__":
    app.run(debug=True, port="5006")