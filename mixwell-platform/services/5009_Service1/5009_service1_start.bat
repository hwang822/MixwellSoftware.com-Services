@echo off
            cd /d %~dp0
            REM Start 5009_service1 on port 5009
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5009') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5009_service1\app.py 5009 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5009_service1\service.log 2>&1"
            echo 5009_service1 started on port 5009
            