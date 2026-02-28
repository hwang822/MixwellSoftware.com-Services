from flask import Flask, request, redirect
import requests

app = Flask(__name__)

AUTH_URL = "http://localhost:5003/api/verify_token"

@app.route("/")
def portal():
    token = request.cookies.get("jwt")
    if not token:
        return redirect("http://localhost:5003/login")

    r = requests.get(AUTH_URL, headers={"Authorization": token})

    if r.status_code != 200:
        return redirect("http://localhost:5003/login")

    return "Welcome to Portal"


if __name__ == "__main__":
    app.run(port=5000)