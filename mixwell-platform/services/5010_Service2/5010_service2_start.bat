@echo off
            cd /d %~dp0
            REM Start 5010_service2 on port 5010
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5010') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            start "" /B cmd /c "C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5010_service2\app.py 5010 >> c:\workarea\mixwellsoftware.com-services\mixwell-platform\services\5010_service2\service.log 2>&1"
            echo 5010_service2 started on port 5010
            