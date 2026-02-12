import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flask import Flask
from services.RDPService.rdpService import rdpService
app = Flask(__name__)

app.register_blueprint(rdpService, url_prefix="/rdp")

if __name__ == "__main__":
    app.run(debug=True, port="5007") 