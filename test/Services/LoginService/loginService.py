from flask import Blueprint, render_template, request

login_bp = Blueprint(
    "login",
    __name__,
    template_folder="templates"
)

@login_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        print("Login attempt:", username)

    return render_template("login.html")
