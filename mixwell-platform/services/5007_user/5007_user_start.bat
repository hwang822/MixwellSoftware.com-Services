@echo off
            cd /d %~dp0
            REM Start 5007_user on port 5007
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5007') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5007_user\app.py 5007 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5007_user\service.log 2>&1"
            echo 5007_user started on port 5007
            