@echo off
            cd /d %~dp0
            REM Stop 5007_user on port 5007
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5007') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5007_user stopped
            