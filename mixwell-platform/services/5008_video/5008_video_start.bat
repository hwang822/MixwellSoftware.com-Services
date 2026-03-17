@echo off
            cd /d %~dp0
            REM Start 5008_video on port 5008
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5008') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5008_video\app.py 5008 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5008_video\service.log 2>&1"
            echo 5008_video started on port 5008
            