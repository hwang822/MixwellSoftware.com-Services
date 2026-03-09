from flask import Flask
from emailService import emailService
app = Flask(__name__)

app.register_blueprint(emailService, url_prefix="/email")

if __name__ == "__main__":
    app.run(debug=True, port="5004")