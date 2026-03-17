@echo off
            cd /d %~dp0
            REM Start 5002_cam on port 5002
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5002') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" /B cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5002_cam\app.py 5002 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5002_cam\service.log 2>&1"
            echo 5002_cam started on port 5002
            