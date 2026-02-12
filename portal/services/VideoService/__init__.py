import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flask import Flask
from services.VideoService.videoService import videoService
app = Flask(__name__)

app.register_blueprint(videoService, url_prefix="/video")

if __name__ == "__main__":
    app.run(debug=True, port="5003")  # Test app port 5003