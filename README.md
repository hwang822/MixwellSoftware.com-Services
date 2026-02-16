Reinstall Python 11  
Python 12+ not support Kivy

control pannel 
uninstall python 14
Delete C:\Users\hwang\AppData\Roaming\Python\Python14

https://www.python.org/downloads/release/python-31114/
Download python 12

requirements.txt

1️⃣ Upgrade pip, setuptools, wheel
python -m pip install --upgrade pip setuptools wheel

2️⃣ Core Flask stack (Portal + DB + Login + WebSockets)
pip install flask             # Portal backend
pip install flask-login       # User login management
pip install flask-sqlalchemy  # Database
pip install flask-socketio    # SocketIO
pip install eventlet          # SocketIO server support

3️⃣ Client / Service support
pip install requests          # API calls from Kivy client / services
pip install opencv-python     # OpenCV (cv2) for any service image/video processing

4️⃣ Kivy client
pip install kivy[base]        # Kivy core
pip install kivy_examples     # optional, for example apps

python -m pip install --upgrade pip setuptools wheel
