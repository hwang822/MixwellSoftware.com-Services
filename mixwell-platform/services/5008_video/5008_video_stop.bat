@echo off
            cd /d %~dp0
            REM Stop 5008_video on port 5008
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5008') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5008_video stopped
            