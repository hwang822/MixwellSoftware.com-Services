@echo off
            cd /d %~dp0
            REM Start 5000_portal on port 5000
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5000') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" /B cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5000_portal\app.py 5000 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5000_portal\service.log 2>&1"
            echo 5000_portal started on port 5000
            