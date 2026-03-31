import os, sys
from flask import Blueprint, Flask, render_template, request, send_from_directory, abort, render_template_string

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')

shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

serviceport = int(app.root_path.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

#app = Flask(__name__)
#serviceport = int(sys.argv[1])
#servicedb = sys.argv[2]
#app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 
current_path = app.root_path

videoService = Blueprint("videoService", __name__)
#current_path = os.path.join(videoService.root_path, "Videos")
#current_path = os.getcwd()  # Get current working directory
print(current_path)
# ---------------- 配置 ----------------
VIDEO_FOLDER = f"{current_path}/videos"   # 视频文件夹路径（可用绝对路径）
PASSWORD = "huaizhong"    # 自定义访问密码
#PORT = 8080               # 服务器端口
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
VIDEO_FOLDER = "D:\\Videos\\201509_Germney_Swiss_VivoVidio"
@videoService.route("/", methods=["GET", "POST"])
def video_home():
    videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4','.mov','.mkv'))]#                                              
    ##return render_template_string("video.html", videos=videos, servicename="Video Service")
    return render_template("video.html", videos = videos, servicename = "Video Service")
"""    
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
"""

@videoService.route("/video/<path:filename>")
def serve_video(filename):
    # 只允许视频文件访问
    if not filename.lower().endswith(('.mp4','.mov','.mkv')):
        abort(403)
    return send_from_directory(VIDEO_FOLDER, filename)

def create_app():
    #app = Flask(__name__)
    app.register_blueprint(videoService)
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)