@echo off
            cd /d %~dp0
            REM Start 5006_registry on port 5006
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5006') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5006_registry\app.py 5006 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5006_registry\service.log 2>&1"
            echo 5006_registry started on port 5006
            