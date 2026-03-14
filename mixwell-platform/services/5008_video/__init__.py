from flask import Flask
from videoService import videoService
app = Flask(__name__)

app.register_blueprint(videoService, url_prefix="/video")

if __name__ == "__main__":
    app.run(debug=True, port="5003")