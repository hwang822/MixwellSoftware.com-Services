@echo off
            cd /d %~dp0
            REM Stop 5006_registry on port 5006
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5006') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5006_registry stopped
            