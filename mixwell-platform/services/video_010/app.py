import os
import sys

from flask import (
    Blueprint,
    Flask,
    abort,
    render_template,
    send_from_directory,
    request,
    redirect
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

VIDEO_FOLDERS = {

    "kids": [

        {
            "name": "Bowen_1",
            "video_name": "Bowen_1",
            "hls_root": r"D:\Videos\199701_Bowen\mp4\hls",
            "hls_folder": r"bowen_1"
        },

        {
            "name": "Bowen_2_1",
            "video_name": "Bowen_2_1",
            "hls_root": r"D:\Videos\199701_Bowen\mp4\hls",
            "hls_folder": r"bowen_2_1"
        },

        {
            "name": "Bowen_2_2",
            "video_name": "Bowen_2_2",
            "hls_root": r"D:\Videos\199701_Bowen\mp4\hls",
            "hls_folder": r"bowen_2_2"
        },

        {
            "name": "Bowen_3_1",
            "video_name": "Bowen_3_1",
            "hls_root": r"D:\Videos\199701_Bowen\mp4\hls",
            "hls_folder": r"bowen_3_1"
        },

    ],

    "family": [
        {
            "name": "family_1",
            "video_name": "family_1",
            "hls_root": r"D:\family\mp4\hls",
            "hls_folder": r"family_1"
        },
    ],

    "travel": [
        {
            "name": "Germany & Switzerland 2015",
            "video_name": "201509_Germney_Swiss_VivoVidio",
            "hls_root": r"D:\Videos\201509_Germney_Swiss_VivoVidio\hls",
            "hls_folder": r"201509_Germney_Swiss_VivoVidio"
        },
    ],

    "sharing": [
        {
            "name": "sharing_1",
            "video_name": "sharing_1",
            "hls_root": r"D:\sharing\mp4\hls",
            "hls_folder": r"sharing_1"
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
@videoService.route("/list/<category>")
def video_list(category):

    videos = VIDEO_FOLDERS.get(category)

    if not videos:
        return "Invalid Category"

    return render_template(
        "video_list.html",
        category=category,
        videos=videos
    )


# ---------------------------------------------------
# Stream Video
# ---------------------------------------------------

@videoService.route(
    "/video/<category>/<int:folder_id>/<path:filename>"
)
def serve_video(
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
        video_name=video["video_name"]
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