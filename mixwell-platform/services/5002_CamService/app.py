
import os, sys
from flask import Flask, redirect, render_template, request
import jwt
import cv2  # pip install opencv-python
from flask import Flask, Blueprint, Response, render_template

BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5002
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')
camService = Blueprint("camService", __name__)


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import db
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(servicePort)
authUrl = f"{Config.SERVICE_URL}:{Config.PORTAL_PORT}/login?service={serviceName}&next={Config.SERVICE_URL}:{servicePort}"
"""
@app.route("/")
def home():    
    user =  get_user()
    if not user:
        return redirect(authUrl) 
    print(f"Welcome {user['email']} using {user['servicename']}")
    return render_template(f"{serviceName}.html") 
"""

def get_user():     
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        user = f"{payload['userid']} + {payload['email']} + {payload['servicename']}"
    except:
        return None        
    return payload


# 这里改成你的DroidCam在PC端的设备号或IP
# 如果PC端DroidCam已经显示为摄像头，比如 /dev/video0 或 0
# Windows上通常是 0, 1, 2...
cap = cv2.VideoCapture(0)   # from laptop  

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # 编码为 JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # 返回多部分 JPEG 流 (mjpeg)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@camService.route("/")
def cam_home():
    #return "Cam Service: Internal Only"
    user =  get_user()
    if not user:
        return redirect(authUrl) 
    print(f"Welcome {user['email']} using {user['servicename']}")
    return render_template(f"{serviceName}.html") 

    #return render_template("CamService.html")

@camService.route('/video_feed')
def video_feed():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

def create_app():
    app = Flask(__name__)
    app.register_blueprint(camService)
    return app



if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=servicePort)
    #with app.app_context():        
    #    create_app()    
    #app.run(port=servicePort)



"""
import cv2
from flask import Flask, Blueprint, Response, render_template
import os
import sys
from flask import Flask, Blueprint

BASE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5002
os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{BASE_PORT}\') do taskkill /F /PID %a')
camService = Blueprint("camService", __name__)

# 这里改成你的DroidCam在PC端的设备号或IP
# 如果PC端DroidCam已经显示为摄像头，比如 /dev/video0 或 0
# Windows上通常是 0, 1, 2...
cap = cv2.VideoCapture(0)   # from laptop  

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # 编码为 JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # 返回多部分 JPEG 流 (mjpeg)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@camService.route("/")
def cam_home():
    #return "Cam Service: Internal Only"
    return render_template("CamService.html")

@camService.route('/video_feed')
def video_feed():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

def create_app():
    app = Flask(__name__)
    app.register_blueprint(camService)
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=BASE_PORT)    

"""    