from flask import Flask
from camService import camService
app = Flask(__name__)
app.register_blueprint(camService, url_prefix="/cam")

if __name__ == "__main__":
    app.run(debug=True, port="5002") 