from flask import Flask, Blueprint

app = Flask(__name__)
bp = Blueprint("test", __name__)

@app.route("/")
def home():
    return "Flask OK"

if __name__ == "__main__":
    app.run(port=8080)