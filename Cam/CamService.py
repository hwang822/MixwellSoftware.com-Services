from flask import Flask, Response
import cv2

app = Flask(__name__)

# 这里改成你的DroidCam在PC端的设备号或IP
# 如果PC端DroidCam已经显示为摄像头，比如 /dev/video0 或 0
# Windows上通常是 0, 1, 2...
cap = cv2.VideoCapture(0)   # from laptop  
#cap = cv2.VideoCapture('http://192.168.12.214:4747/video')

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

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return """
    <html>
        <body>
            <h1>Home Cam</h1>
            <img src="/video_feed">
        </body>
    </html>
    """

if __name__ == "__main__":
    # host='0.0.0.0' 让局域网其他设备访问
    app.run(host='0.0.0.0', port=8030)