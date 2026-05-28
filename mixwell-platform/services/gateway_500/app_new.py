import os
import sys
from flask import Blueprint, Flask, Response, redirect, request
import requests

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

app = Flask(
    __name__,
    static_folder=os.path.join(base_dir, 'static'),
    static_url_path='/static'
)

sys.path.insert(0, f"{app.root_path}/../../")
from config.settings import Config
from models import Utility, db

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport

portalport = int(serviceport/1000)*1000
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/auth_{portalport}"
portalurl = Config.PORTAL_PUBLIC_URL
serviceurl = Config.GATEWAY_PUBLIC_URL


gatewayService = Blueprint("gatewayService", __name__)


@app.route(
    "/service/<servicename>",
    defaults={"path": ""},
    methods=["GET","POST","PUT","DELETE","PATCH"]
)

@app.route(
    "/service/<servicename>/<path:path>",
    methods=["GET","POST","PUT","DELETE","PATCH"]
)
def route_service(servicename, path):

    try:

        user = Utility.user_check(servicename)

        if not user:

            authurl = (
                f"{portalurl}/login?next={serviceurl}/service/{servicename}"
            )
            return redirect(authurl)

        service = Utility.service_get(servicename)

        if not service:
            return "service not found", 404

        base_url = service.url.rstrip("/")

        target_url = f"{base_url}/{path}" if path else base_url

        # preserve query string
        if request.query_string:
            target_url += "?" + request.query_string.decode()

        headers = {
            key: value
            for key, value in request.headers
            if key.lower() != "host"
        }

        # ⭐ VERY IMPORTANT
        headers["X-Forwarded-Prefix"] = f"/service/{servicename}"

        r = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            stream=True,
            allow_redirects=False
        )

        excluded_headers = [
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        ]

        response_headers = [
            (name, value)
            for (name, value) in r.raw.headers.items()
            if name.lower() not in excluded_headers
        ]

        return Response(
            r.content,
            r.status_code,
            response_headers
        )

    except Exception as e:
        print(e)
        return str(e), 500

def create_app():
    app.register_blueprint(gatewayService)
    return app

if __name__ == "__main__":
    with app.app_context(): 
        app.config["SQLALCHEMY_DATABASE_URI"] = auth_db 
        db.init_app(app)    
    print (f"run gateway service at {serviceport}")    
    create_app().run(host="0.0.0.0", port=serviceport, debug=False, use_reloader=False)
    # host="0.0.0.0" for extern expose