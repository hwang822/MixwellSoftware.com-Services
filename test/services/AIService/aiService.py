from flask import Blueprint, render_template, request
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

aiService = Blueprint(
    "aiService",
    __name__,
    template_folder="templates"
)

@aiService.route("/", methods=["GET", "POST"])
def AIService():
    if request.method == "POST":
        username = request.form.get("username")
        print("AIService attempt:", username)

    return render_template("AIService.html")
