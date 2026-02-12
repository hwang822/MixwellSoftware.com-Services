from flask import Flask
from Services.AIService.aiService import aiService
app = Flask(__name__)

app.register_blueprint(aiService, url_prefix="/ai")

if __name__ == "__main__":
    app.run(debug=True, port="5001")  # Test app port 5001