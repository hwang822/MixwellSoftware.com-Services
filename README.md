Reinstall mixwellsoftware.com services

cd C:\Workarea

C:\Workarea
install python 3.12.0 at https://www.python.org/downloads/windows/?utm_source=chatgpt.com


git clone 

(venv) C:\Workarea\MixwellSoftware.com-Services\mixwell-platform>python --version
Python 3.12.0 https://github.com/hwang822/MixwellSoftware.com-Services
to C:\Workarea\MixwellSoftware.com-Services folder.
删除 build 目录里的 venv，然后重新创建。
cd C:\Workarea\MixwellSoftware.com-Services\build\MixwellSoftware.com-Services\mixwell-platform
rmdir /s /q venv

py -3.12 -m venv venv
venv\Scripts\python.exe
就会绑定当前 miniPC 的 Python 3.12。

venv\Scripts\activate

python -m pip install --upgrade pip

pip install -r requirements.txt

may need install some missed item.

pip install pywebview flask pytz


✅ 正确生成 requirements.txt

在你的 dev 环境 里运行：

venv\Scripts\pip freeze > requirements.txt and copy to github for build to use build dependentments.





*******************************************
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

################################################
Perfect — now you are at distribution stage. Let’s go step by step.

You have:

aiservice.exe    → Windows
aiservice.apk    → Android
aiservice.ipa    → iOS

And you want:

3 QR codes on your portal → users scan → download/install

1️⃣ Step 1 — 放置安装文件
Windows APK / EXE

Put aiservice.exe somewhere publicly accessible:

https://www.mixwellsoftware.com/downloads/aiservice.exe

Put aiservice.apk somewhere publicly accessible:

https://www.mixwellsoftware.com/downloads/aiservice.apk

iOS IPA:
⚠ iOS 不能直接下载 IPA for App Store users
Options:

TestFlight (Apple official)

Upload IPA → TestFlight → invite users

Share TestFlight QR

Enterprise distribution (requires Apple Enterprise account)

2️⃣ Step 2 — 生成 QR Codes

You can use Python to generate QR codes easily:

import qrcode

# Example mapping
apps = {
    "Windows": "https://www.mixwellsoftware.com/downloads/aiservice.exe",
    "Android": "https://www.mixwellsoftware.com/downloads/aiservice.apk",
    "iOS": "https://testflight.apple.com/join/YourAppCode"
}

for name, url in apps.items():
    img = qrcode.make(url)
    img.save(f"{name}_QR.png")
    print(f"{name} QR saved")

This produces:

Windows_QR.png
Android_QR.png
iOS_QR.png