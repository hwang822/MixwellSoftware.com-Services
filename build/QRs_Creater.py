import qrcode

# python -m pip install qrcode[pil]

# Example mapping
apps = {
    "Windows": "https://www.mixwellsoftware.com/apps/windows/dist/aiservice.exe"
    #"Android": "https://www.mixwellsoftware.com/apps/android/aiservice.apk"
    #"iOS": "https://testflight.apple.com/join/YourAppCode"
}

for name, url in apps.items():
    img = qrcode.make(url)
    img.save(f"{name}_QR.png")
    print(f"{name} QR saved")