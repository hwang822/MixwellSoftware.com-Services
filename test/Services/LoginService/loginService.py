from flask import Blueprint, render_template, request

loginService = Blueprint(
    "login",
    __name__,
    template_folder="templates"
)

@loginService.route("/", methods=["GET", "POST"])
def LoginService():
    if request.method == "POST":
        username = request.form.get("username")
        print("Login attempt:", username)

    return render_template("login.html")
