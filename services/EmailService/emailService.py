from flask import Flask, Blueprint, render_template, request

emailService = Blueprint("emailService", __name__)

def send_email():
    return "Email Sent!"

@emailService.route("/")
def Email_home():
    return render_template("EmailService.html")

@emailService.route("/email/", methods=["GET", "POST"])
def sendEmail():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        msg = request.form.get("message")        
        return send_email()

    return render_template("EmailService.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(emailService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5004)