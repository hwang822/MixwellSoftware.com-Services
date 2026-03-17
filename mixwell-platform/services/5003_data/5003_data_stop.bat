@echo off
            cd /d %~dp0
            REM Stop 5003_data on port 5003
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5003') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5003_data stopped
            