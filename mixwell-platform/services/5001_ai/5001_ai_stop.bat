@echo off
            cd /d %~dp0
            REM Stop 5001_ai on port 5001
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5001') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5001_ai stopped
            