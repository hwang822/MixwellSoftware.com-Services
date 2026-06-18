
import json
import os
import sys
from cruise_map import build_map

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

cruiseService = Blueprint(
    "cruiseService",
    __name__
)



# ---------------------------------------------------
# Home
# ---------------------------------------------------

@cruiseService.route("/")
def cruise_home():

    cruises = []

    data_dir = os.path.join(
        app.root_path,
        "data"
    )

    for f in os.listdir(data_dir):

        if f.lower().endswith(".csv"):

            cruises.append(
                os.path.splitext(f)[0]
            )

    cruises.sort()

    return render_template(
        "cruises.html",
        cruises=cruises,
        servicename="Cruise Service"
    )

#@cruiseService.route("/service/cruise/view/<name>")
#def cruise_view_serv(name):
#    return cruise_view(name)

@cruiseService.route("/view/<name>")
def cruise_view(name):

    print("VIEW =", name)

    html_file = os.path.join(
        app.root_path,
        "generated",
        f"cruise_map_{name}.html"
    )

    json_file = os.path.join(
        app.root_path,
        "cache",
        f"{name}.json"
    )

    csv_file = os.path.join(
        app.root_path,
        "data",
        f"{name}.csv"
    )

    if not os.path.exists(csv_file):
        print("CSV NOT FOUND")
        abort(404)
    
    itinerary = []

    if (
        not os.path.exists(html_file)
        or os.path.getmtime(csv_file)
           > os.path.getmtime(html_file)
    ):
        print("Building map...")
        build_map(app.root_path, csv_file, json_file, html_file)


    if os.path.exists(json_file):

        with open(
            json_file,
            encoding="utf-8"
        ) as f:

            itinerary = json.load(f)
    print("html_file = ", html_file)
    return render_template(
        "cruises_view.html",
        map_file=os.path.basename(html_file),
        cruise_name=name,
        itinerary=itinerary,
        servicename="Cruise Service"
    )


@cruiseService.route("/generated/<path:filename>")
def generated_file(filename):

    return send_from_directory(
        os.path.join(app.root_path, "generated"),
        filename
    )

# ---------------------------------------------------
# Create App
# ---------------------------------------------------
def create_app():

    app.register_blueprint(
        cruiseService
    )
    return app

# ---------------------------------------------------

if __name__ == "__main__":
    create_app().run(
        host=Config.SERVICE_BIND_HOST_EXTERNAL,
        port=serviceport,
        debug=False,
        use_reloader=False
    )


    