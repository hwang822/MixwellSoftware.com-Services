@echo off
            cd /d %~dp0
            REM Stop 5002_cam on port 5002
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5002') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5002_cam stopped
            