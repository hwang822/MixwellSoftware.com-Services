@echo off
            cd /d %~dp0
            REM Start 5004_email on port 5004
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5004') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" /B cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5004_email\app.py 5004 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5004_email\service.log 2>&1"
            echo 5004_email started on port 5004
            