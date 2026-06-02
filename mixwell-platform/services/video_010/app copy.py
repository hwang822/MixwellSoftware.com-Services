import os, sys
from flask import Blueprint, Flask, abort, render_template, send_from_directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from models import db

app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')
shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport

current_path = app.root_path

videoService = Blueprint("videoService", __name__)
print(current_path)
# ---------------- 配置 ----------------
VIDEO_FOLDER = f"{current_path}/videos"   # 视频文件夹路径（可用绝对路径）
# --------------------------------------

VIDEO_FOLDER = "D:\\Videos\\201509_Germney_Swiss_VivoVidio"
@videoService.route("/", methods=["GET", "POST"])
def video_home():
    print("******** VIDEO_HOME CALLED ********")
    videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4','.mov','.mkv'))]#                                              
    print (videos)
    return render_template("video.html", videos = videos, servicename = "Video Service")

@videoService.route("/service/video/", methods=["GET", "POST"])
def video_home_serv():
    return video_home()


@videoService.route("/video/<path:filename>")
def serve_video(filename):
    # 只允许视频文件访问
    if not filename.lower().endswith(('.mp4','.mov','.mkv')):
        abort(403)
    return send_from_directory(VIDEO_FOLDER, filename)

@videoService.route("/service/video/video/<path:filename>")
def serve_video_api(filename):
    return serve_video(filename)

def create_app():    
    app.register_blueprint(videoService)
    
    print("\n========== ROUTES ==========")
    print(app.url_map)
    print("============================\n")

    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host=Config.SERVICE_BIND_HOST_EXTERNAL, port=serviceport,  debug=False, use_reloader=False)