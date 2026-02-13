from flask import Flask
from dataAPIService import dataAPIService
app = Flask(__name__)

app.register_blueprint(dataAPIService, url_prefix="/dataAPI")

if __name__ == "__main__":
    app.run(debug=True, port="5006")