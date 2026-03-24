import sys
from flask import Flask, redirect

app = Flask(__name__)

BASE_DIR = f"{app.root_path}/../../"  
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from models import Utility, db

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]

gatewayport = int(serviceport/1000)*1000 + 500

auth_db = f"{Config.SQLALCHEMY_DATABASE_URI}/auth_{gatewayport}"
app.config["SQLALCHEMY_DATABASE_URI"] = auth_db 
db.init_app(app)    
authurl = f"http://localhost:{serviceport}"
@app.route("/service/<servicename>")  #services.mixwellsoftware.com/service/servicename
def route_service(servicename):
    try:
        # ✅ 1. 验证用户
        user = Utility.user_check(servicename)    
        if not user:
            return redirect(f"{authurl}/login?next=/service/{servicename}")    

        # ✅ 2. 查 service 信息（DB）
        service = Utility.service_get(servicename)
        if not service:
            return "Service not found", 404
        return redirect(f"{service.url}")

        # ✅ 3. 记录访问
        #record_user_service(user.id, service.id)
            #did at 1. 验证用户

        # ✅ 4. 转发（proxy）
        # url = service.url   # e.g. http://localhost:8001
        # resp = requests.get(url, cookies=request.cookies)

        #return resp.text

    except Exception as e:
        Utility.notify_support(service, str(e))
        return "Sorry, service is not available at the moment", 500


if __name__ == "__main__":
    print (f"run gateway service at {serviceport}")    
    app.run(port=gatewayport, debug=False, use_reloader=False)
