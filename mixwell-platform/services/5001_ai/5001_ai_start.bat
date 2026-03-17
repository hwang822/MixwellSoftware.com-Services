@echo off
            cd /d %~dp0
            REM Start 5001_ai on port 5001
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5001') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" /B cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5001_ai\app.py 5001 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5001_ai\service.log 2>&1"
            echo 5001_ai started on port 5001
            