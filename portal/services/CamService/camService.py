
import cv2
from flask import Flask, Blueprint, Response, render_template
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
    create_app().run(host="127.0.0.1", port=5002)    