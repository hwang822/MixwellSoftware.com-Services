@echo off
            cd /d %~dp0
            REM Stop 5000_portal on port 5000
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5000') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5000_portal stopped
            