import os
import sys
from flask import Blueprint, Flask, Response, redirect
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

#serviceport = int(app.root_path.rsplit("_")[1]) + 5000
#serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

portalport = int(serviceport/1000)*1000
portalurl = Config.GATEWAY_URL
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/auth_{portalport}"
serviceurl = f"{Config.GATEWAY_URL}:{serviceport}"

gatewayService = Blueprint("gatewayService", __name__)
@app.route("/service/<servicename>", defaults={"path": ""})
@app.route("/service/<servicename>/<path:path>")
def route_service(servicename, path):
    try:
        user = Utility.user_check(servicename)
        if not user:
            authusl = f"{portalurl}:{portalport}/login?next={serviceurl}/service/{servicename}"
            return redirect(authusl)

        service = Utility.service_get(servicename)
        base_url = service.url.rstrip("/")
        
        #build full target URL
        target_url = f"{base_url}/{path}" if path else base_url
        r = requests.get(target_url, stream=True)
    
        def generate():
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            content_type=r.headers.get("Content-Type")
        )

    except Exception as e:
        print(e)
        return str(e)

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