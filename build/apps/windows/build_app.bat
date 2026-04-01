@echo off
cd /d %~dp0
REM pyinstaller --onefile --noconsole --icon=logo.ico app_portal.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_ai.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_data.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_email.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_rdp.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_registry.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_service1.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_service2.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_user.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_video.py
REM pyinstaller --onefile --noconsole --icon=logo.ico app_cam.py
pyinstaller --onefile --noconsole --icon=logo.ico app_tesla.py
