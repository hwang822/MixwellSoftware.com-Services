import sys
from flask import Flask, Response, redirect
import requests

app = Flask(__name__)

BASE_DIR = f"{app.root_path}/../../"  
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from models import Utility, db

serviceport = int(Config.GATEWAY_PORT)
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

portalport = int(serviceport/1000)*1000
portalurl = Config.SERVICE_URL
auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/auth_{portalport}"

@app.route("/service/<servicename>", defaults={"path": ""})
@app.route("/service/<servicename>/<path:path>")
def route_service(servicename, path):
    try:
        service = Utility.service_get(servicename)
        base_url = service.url.rstrip("/")

        # build full target URL
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

if __name__ == "__main__":
    with app.app_context(): 
        app.config["SQLALCHEMY_DATABASE_URI"] = auth_db 
        db.init_app(app)    
    print (f"run gateway service at {serviceport}")    
    app.run(port=serviceport, debug=False, use_reloader=False)
