import glob
import os
import shutil
import sys
import time
import uuid
import subprocess


from flask import (
    Blueprint,
    Flask,
    abort,
    render_template,
    send_from_directory,
    request,
    redirect
)

LIVE_ROOT = r"C:\Temp\live_hls"

os.makedirs(
    LIVE_ROOT,
    exist_ok=True
)

LIVE_ROOT = r"C:\Temp\live_hls"

for name in os.listdir(LIVE_ROOT):

    folder = os.path.join(LIVE_ROOT, name)

    if not os.path.isdir(folder):
        continue

    age_hours = (
        time.time()
        - os.path.getmtime(folder)
    ) / 3600

    if age_hours > 10:

        print("Delete old session:", folder)

        shutil.rmtree(
            folder,
            ignore_errors=True
        )


# ---------------------------------------------------
# Base
# ---------------------------------------------------

base_dir = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../"
    )
)

sys.path.insert(0, base_dir)

from config.settings import Config
from models import db

app = Flask(
    __name__,
    static_folder=os.path.join(
        base_dir,
        "static"
    ),
    static_url_path="/static"
)

shared_templates = os.path.abspath(
    os.path.join(
        base_dir,
        "templates"
    )
)

app.jinja_loader.searchpath.append(
    shared_templates
)

print(
    "Shared templates:",
    shared_templates
)

baseport = int(Config.PORTAL_PORT)

baseport = (
    int(sys.argv[1])
    if len(sys.argv) > 1
    else baseport
)

serviceport = (
    int(app.root_path.rsplit("_")[1])
    + baseport
)

videoService = Blueprint(
    "videoService",
    __name__
)


# ---------------------------------------------------
# Video Folders
# ---------------------------------------------------
VIDEO_DRIVE = "D:"
if Config.TEST:    
    VIDEO_DRIVE = "C:"
VIDEO_FOLDERS = {

    "kids": [

        {
            "name": "Bowen_1",
            "video_name": "Bowen_1",
            "mp4_path": VIDEO_DRIVE + r"\Videos\199701_Bowen\1997_Bowen_1\Bowen_1.mp4",
        },

        {
            "name": "Bowen_2_1",
            "video_name": "Bowen_2_1",
            "mp4_path": VIDEO_DRIVE + r"\Videos\\199701_Bowen\1997_Bowen_2_1\Bowen_2_1.mp4",
        },
    
        {
            "name": "Bowen_2_2",
            "video_name": "Bowen_2_2",
            "mp4_path": VIDEO_DRIVE + r"\Videos\199701_Bowen\1997_Bowen_2_2\Bowen_2_2.mp4",
        },

        {
            "name": "Bowen_3_1",
            "video_name": "Bowen_3_1",
            "mp4_path": VIDEO_DRIVE + r"\Videos\199701_Bowen\1997_Bowen_3_1\Bowen_3_1.mp4",
        },

    ],

    "family": [
        {
            "name": "family_1",
            "video_name": "family_1",
            "mp4_path": VIDEO_DRIVE + r"\family\family.mp4",
        },
    ],

    "travel": [
        {
            "name": "20251027 江西安徽",
            "video_name": "20251027 江西安徽",
            "mp4_path": VIDEO_DRIVE + r"\Photos\20251006_China\20251027_江西安徽\20251027_江西安徽.mp4",
        },
        {
            "name": "20251210 新疆",
            "video_name": "20251210 新疆",
            "mp4_path": VIDEO_DRIVE + r"\Photos\20251006_China\20251210_新疆\20251210_新疆.mp4",
        },
        {
            "name": "201509 Germney Swiss",
            "video_name": "201509 Germney Swiss",
            "mp4_path": VIDEO_DRIVE + r"\Photos\201509_Germney_Swiss_VivoVidio\201509_Germney_Swiss_VivoVidio.mp4",
        },

    ],

    "sharing": [
        {
            "name": "20251027 江西安徽",
            "video_name": "20251027 江西安徽",
            "mp4_path": VIDEO_DRIVE + r"\Photos\20251006_China\20251027_江西安徽\20251027_江西安徽.mp4",
        },
        {
            "name": "20251210 新疆",
            "video_name": "20251210 新疆",
            "mp4_path": VIDEO_DRIVE + r"\Photos\20251006_China\20251210_新疆\20251210_新疆.mp4",
        },
        
    ]
}

# ---------------------------------------------------
# Users
# ---------------------------------------------------

VIDEO_USERS = {

    "family": {
        "username": "family",
        "password": "123"
    },

    "kids": {
        "username": "kids",
        "password": "123"
    },

    "travel": {
        "username": "travel",
        "password": "123"
    },

    "sharing": {
        "username": "guest",
        "password": "123"
    }
}

# ---------------------------------------------------
# Home
# ---------------------------------------------------

@videoService.route("/")
def video_home():

    return render_template(
        "video.html",
        servicename="Video Service"
    )

# ---------------------------------------------------
# Login
# ---------------------------------------------------

@videoService.route(
    "/login",
    methods=["POST"]
)
def video_login():

    category = request.form.get(
        "category"
    )

    username = request.form.get(
        "username"
    )

    password = request.form.get(
        "password"
    )

    cfg = VIDEO_USERS.get(category)

    if not cfg:
        return "Invalid Category"

    if (
        username == cfg["username"]
        and password == cfg["password"]
    ):

        return redirect(
            f"/list/{category}"
        )

    return "Login Failed"

# ---------------------------------------------------
# Video List
# ---------------------------------------------------

@videoService.route("/list/<category>")
def video_list(category):

    videos = VIDEO_FOLDERS.get(category)

    if not videos:
        return "Invalid Category"

    return render_template(
        "video_list.html",
        category=category,
        videos=videos,
        servicename="Video Service"
    )

# ---------------------------------------------------
# play living
# ---------------------------------------------------
@videoService.route("/play_live/<category>/<int:video_id>")
def play_live(category, video_id):
    try:
        videos = VIDEO_FOLDERS.get(category)
        if not videos:
            abort(404)
        video = videos[video_id]
        session_id = uuid.uuid4().hex
        folder = os.path.join(
            LIVE_ROOT,
            session_id
        )
        os.makedirs(folder, exist_ok=True)
        playlist = os.path.join(
            folder,
            "index.m3u8"
        )
        segment_pattern = os.path.join(
            folder,
            "index%03d.ts"
        )
        cmd = [
            "ffmpeg",
            "-re",
            "-i", video["mp4_path"],

            "-c:v", "libx264",
            "-preset", "veryfast",
            "-vf", "scale=1920:-2",
            "-pix_fmt", "yuv420p",

            "-g", "60",
            "-keyint_min", "60",
            "-sc_threshold", "0",

            "-c:a", "aac",
            "-b:a", "128k",

            "-f", "hls",
            "-hls_time", "2",

            # 🔥 THIS is the sliding window size
            "-hls_list_size", "30",

            # 🔥 THIS enables deletion of old segments
            "-hls_flags", "delete_segments+independent_segments",

            "-hls_segment_filename", segment_pattern,
            playlist
        ]

        print("START FFMPEG")
        print(cmd)
        subprocess.Popen(cmd)
        print("SESSION=", session_id)
        print("PLAYLIST=", playlist)                
        
        for i in range(150):

            ts_count = len(
                glob.glob(
                    os.path.join(folder,"*.ts")
                )
            )

            if ts_count >= 4:
                break

            time.sleep(0.1)


        return render_template(
            "video_hls.html",
            src=f"/live/{session_id}/index.m3u8",
            video_name=video["video_name"],
            servicename="Video Service"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e)

@videoService.route("/live/<session_id>/<path:filename>")
def serve_live(session_id, filename):
    folder = os.path.join(
        LIVE_ROOT,
        session_id
    )
    return send_from_directory(
        folder,
        filename
    )

#
# ---------------------------------------------------
# Stream Video
# ---------------------------------------------------
from flask import send_file
@videoService.route("/video/<category>/<int:video_id>")
def serve_video(category, video_id):
    videos = VIDEO_FOLDERS.get(category)

    if not videos:
        abort(404)

    if video_id >= len(videos):
        abort(404)

    video = videos[video_id]

    return send_file(
        video["mp4_path"],
        conditional=True
    )

@videoService.route(
    "/video/<category>/<int:folder_id>/<path:filename>"
)
def serve_video_hls(
    category,
    folder_id,
    filename
):

    folders = VIDEO_FOLDERS.get(
        category
    )

    if not folders:
        abort(404)

    if folder_id >= len(folders):
        abort(404)

    folder = folders[
        folder_id
    ]

    full_path = os.path.join(
        folder,
        filename
    )

    if not os.path.isfile(
        full_path
    ):
        abort(404)

    return send_from_directory(
        folder,
        filename
    )

# --------------------------------------------------
# Create hls play
#---------------------------------------------------
@videoService.route("/hls/<category>/<int:video_id>/<path:filename>")
def hls(category, video_id, filename):

    video = VIDEO_FOLDERS[category][video_id]

    folder = os.path.join(
        video["hls_root"],
        video["hls_folder"]
    )

    return send_from_directory(folder, filename)

@videoService.route("/play_hls/<category>/<int:video_id>")
def play_hls(category, video_id):
    video = VIDEO_FOLDERS[category][video_id]
    return render_template(
        "video_hls.html",
        src=f"/hls/{category}/{video_id}/index.m3u8",
        video_name=video["video_name"],
        servicename="Video Service"
    )

# --------------------------------------------------
# Create mp4 play
#---------------------------------------------------

@videoService.route("/play_video/<category>/<int:video_id>")
def play_video(category, video_id):

    videos = VIDEO_FOLDERS.get(category)

    if not videos:
        abort(404)

    if video_id >= len(videos):
        abort(404)

    video = videos[video_id]

    return render_template(
        "video_player.html",
        category=category,
        video_id=video_id,
        video_name=video["video_name"],
        servicename="Video Service"
    )

# ---------------------------------------------------
# Create App
# ---------------------------------------------------

def create_app():

    app.register_blueprint(
        videoService
    )

    print(
        "\n========== ROUTES =========="
    )
    print(
        app.url_map
    )
    print(
        "============================\n"
    )

    return app

# ---------------------------------------------------

if __name__ == "__main__":
    print(
        f"start running "
        f"{app.root_path} "
        f"at {serviceport}"
    )

    create_app().run(
        host=Config.SERVICE_BIND_HOST_EXTERNAL,
        port=serviceport,
        debug=False,
        use_reloader=False
    )