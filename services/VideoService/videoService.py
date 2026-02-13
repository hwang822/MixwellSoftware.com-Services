from flask import Flask, Blueprint

import os
from flask import Flask, send_from_directory, request, abort, render_template_string
videoService = Blueprint("videoService", __name__)

current_path = os.path.join(videoService.root_path, "Videos")
#current_path = os.getcwd()  # Get current working directory
print(current_path)
# ---------------- 配置 ----------------
VIDEO_FOLDER = current_path  # 视频文件夹路径（可用绝对路径）
PASSWORD = "huaizhong"    # 自定义访问密码
PORT = 8080               # 服务器端口
# --------------------------------------

#app = Flask(__name__)

# HTML 输入密码页面
HTML_PASSWORD = """
<!doctype html>
<title>旅游视频</title>
<h1>请输入访问密码</h1>
<form method="post">
  <input type="password" name="pw" placeholder="密码">
  <input type="submit" value="进入">
</form>
"""

# HTML 视频列表页面
HTML_LIST = """
<!doctype html>
<title>旅游视频列表</title>
<h1>旅游视频</h1>
<ul>
{% for video in videos %}
<li>
  <a href="/video/{{video}}" target="_blank">{{video}}</a>
</li>
{% endfor %}
</ul>
"""

@videoService.route("/", methods=["GET", "POST"])
def video_home():
    if request.method == "POST":
        if request.form.get("pw") == PASSWORD:
            try:
                videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4','.mov','.mkv'))]#                                              
            except FileNotFoundError:
                return "视频文件夹不存在，请检查配置"
            return render_template_string(HTML_LIST, videos=videos)
        else:
            return "密码错误"
    return HTML_PASSWORD

@videoService.route("/video/<path:filename>")
def serve_video(filename):
    # 只允许视频文件访问
    if not filename.lower().endswith(('.mp4','.mov','.mkv')):
        abort(403)
    return send_from_directory(VIDEO_FOLDER, filename)

def create_app():
    app = Flask(__name__)
    app.register_blueprint(videoService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5003)  # localhost only