@echo off
cd /d %~dp0
pyinstaller --onefile --noconsole --icon=logo.ico app_portal.py
pyinstaller --onefile --noconsole --icon=logo.ico app_ai.py
pyinstaller --onefile --noconsole --icon=logo.ico app_data.py
pyinstaller --onefile --noconsole --icon=logo.ico app_email.py
pyinstaller --onefile --noconsole --icon=logo.ico app_rdp.py
pyinstaller --onefile --noconsole --icon=logo.ico app_registry.py
pyinstaller --onefile --noconsole --icon=logo.ico app_service1.py
pyinstaller --onefile --noconsole --icon=logo.ico app_service2.py
pyinstaller --onefile --noconsole --icon=logo.ico app_user.py
pyinstaller --onefile --noconsole --icon=logo.ico app_video.py
