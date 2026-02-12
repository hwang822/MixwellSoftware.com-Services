import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flask import Flask
from services.EmailService.emailService import emailService
app = Flask(__name__)

app.register_blueprint(emailService, url_prefix="/email")

if __name__ == "__main__":
    app.run(debug=True, port="5004")  # Test app port 5004