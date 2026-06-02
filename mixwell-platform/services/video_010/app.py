import os
import sys

from flask import (
    Blueprint,
    Flask,
    abort,
    render_template,
    send_from_directory,
    request,
    redirect,
    session
)

base_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../')
)

app = Flask(
    __name__,
    static_folder=os.path.join(base_dir, 'static'),
    static_url_path='/static'
)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1
)

app.secret_key = "video-secret-key"

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE="Lax"
)



shared_templates = os.path.abspath(
    os.path.join(base_dir, "templates")
)

app.jinja_loader.searchpath.append(shared_templates)

sys.path.insert(0, base_dir)

from config.settings import Config
from models import db

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport

serviceport = int(app.root_path.rsplit("_")[1]) + baseport

videoService = Blueprint("videoService", __name__)

# ---------------------------------------------------
# Video Folder
# ---------------------------------------------------

VIDEO_FOLDER = r"D:\Videos\201509_Germney_Swiss_VivoVidio"

VIDEO_FOLDERS = {
    "kids": [
        r"D:\Videos\199701_Bowen\1997_Bowen_1",
        r"D:\Videos\199701_Bowen\1997_Bowen_2_1",
        r"D:\Videos\199701_Bowen\1997_Bowen_2_2"        
        ],
    "family": [r"D:\Videos\videos_family"],
    "travel": [
            r"D:\Videos\201509_Germney_Swiss_VivoVidio", 
            r"D:\Videos\200709_Bahama",
            r"D:\Videos\201606_Seattle"       
        ],
    "sharing": [r"D:\Videos\videos_sharing"],
}

# ---------------------------------------------------
# Login Users
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

@videoService.route("/testsession")
def testsession():

    from flask import session

    cnt = session.get("cnt", 0)
    cnt += 1

    session["cnt"] = cnt

    return f"cnt={cnt}"

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

@videoService.route("/login", methods=["POST"])
def video_login():
    print("SECRET KEY =", app.secret_key)

    print("HOST =", request.host)
    print("SCHEME =", request.scheme)
    category = request.form.get("category")
    username = request.form.get("username")
    password = request.form.get("password")

    cfg = VIDEO_USERS.get(category)

    if not cfg:
        return "Invalid Category"

    if (
        username == cfg["username"]
        and password == cfg["password"]
    ):
        session[f"video_{category}"] = True
        print("LOGIN SESSION =", dict(session))
        return redirect(
            f"/list/{category}"
        )

    return """
    <h2>Login Failed</h2>
    <a href="/service/video">Back</a>
    """

# ---------------------------------------------------
# Video List
# ---------------------------------------------------

@videoService.route("/list/<category>")
def video_list(category):
    try:
        print("SECRET KEY =", app.secret_key)
        print("HOST =", request.host)
        print("SCHEME =", request.scheme)

        print("SESSION =", dict(session))
        print("LOOKUP =", f"video_{category}")
        print("VALUE =", session.get(f"video_{category}"))        
        
        print("CATEGORY =", category)
        if not session.get(f"video_{category}"):

            return redirect("/")

        folders = VIDEO_FOLDERS.get(category)
        print("FOLDERS =", folders)
        if not folders:
            return "Invalid category", 404

        videos = []

        for folder in folders:
            print("SCAN:", folder)
            if not os.path.exists(folder):
                print(f"Folder not found: {folder}")
                continue

            for f in os.listdir(folder):

                if f.lower().endswith(
                    ('.mp4', '.mov', '.mkv')
                ):

                    videos.append({
                        "filename": f,
                        "folder": folder
                    })

        videos.sort(
            key=lambda x: x["filename"]
        )

        return render_template(
            "video_list.html",
            category=category,
            videos=videos,
            servicename="Video Service"
        )
    except Exception as e:

        import traceback

        traceback.print_exc()

        return str(e), 500
"""
@videoService.route("/list/<category>")
def video_list(category):

    if not session.get(f"video_{category}"):

        return redirect(
            "/service/video"
        )

    videos = sorted([
        f
        for f in os.listdir(VIDEO_FOLDERS.get(category, ""))
        if f.lower().endswith(
            ('.mp4', '.mov', '.mkv')
        )
    ])

    return render_template(
        "video_list.html",
        category=category,
        videos=videos,
        servicename="Video Service"
    )
"""

# ---------------------------------------------------
# Video Stream
# ---------------------------------------------------

@videoService.route("/video/<category>/<path:filename>")
def serve_video(category, filename):

    folders = VIDEO_FOLDERS.get(category)

    if not folders:
        abort(404)

    for folder in folders:

        full_path = os.path.join(
            folder,
            filename
        )

        if os.path.isfile(full_path):

            return send_from_directory(
                folder,
                filename
            )

    abort(404)

"""
@videoService.route("/video/<path:filename>")
def serve_video(filename):

    if not filename.lower().endswith(
        ('.mp4', '.mov', '.mkv')
    ):
        abort(403)

    return send_from_directory(
        VIDEO_FOLDERS.get(filename.split("/")[0], ""),
        filename
    )
"""
# ---------------------------------------------------

def create_app():

    app.register_blueprint(videoService)

    return app

# ---------------------------------------------------

if __name__ == "__main__":

    print(
        f"start running {app.root_path} "
        f"at {serviceport}"
    )

    create_app().run(
        host=Config.SERVICE_BIND_HOST_EXTERNAL,
        port=serviceport
    )

