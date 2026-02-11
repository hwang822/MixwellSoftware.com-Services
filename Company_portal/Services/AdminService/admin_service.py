from flask import render_template, request

def admin_service():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # 这里可以写你的验证逻辑
        print("admin_service:", username)
    return # render_template("admin_service.html")