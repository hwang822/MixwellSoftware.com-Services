from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Demo registered users
USERS = {"user1": "password1", "user2": "password2"}

@app.route("/", methods=["GET", "POST"])
def login():
    return render_template("dashboard.html")
"""    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if USERS.get(username) == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Login failed", 403
    return render_template("login.html")
"""
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # Internal calls to services
    ai_resp = requests.get("http://127.0.0.1:5001/").text
    cam_resp = requests.get("http://127.0.0.1:5002/").text
    video_resp = requests.get("http://127.0.0.1:5003/").text

    return render_template(
        "dashboard.html",
        ai=ai_resp,
        cam=cam_resp,
        video=video_resp
    )

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # public portal