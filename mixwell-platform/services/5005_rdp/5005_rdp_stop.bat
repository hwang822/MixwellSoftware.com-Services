@echo off
            cd /d %~dp0
            REM Stop 5005_rdp on port 5005
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5005') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5005_rdp stopped
            