@echo off
            cd /d %~dp0
            REM Stop 5004_email on port 5004
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5004') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5004_email stopped
            