@echo off
            cd /d %~dp0
            REM Start 5003_data on port 5003
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5003') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" /B cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5003_data\app.py 5003 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5003_data\service.log 2>&1"
            echo 5003_data started on port 5003
            