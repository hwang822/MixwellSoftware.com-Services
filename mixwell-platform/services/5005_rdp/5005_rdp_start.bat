@echo off
            cd /d %~dp0
            REM Start 5005_rdp on port 5005
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5005') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5005_rdp\app.py 5005 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5005_rdp\service.log 2>&1"
            echo 5005_rdp started on port 5005
            