@echo off
            cd /d %~dp0
            REM Stop 5010_service2 on port 5010
            FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :5010') DO (
                taskkill /PID %%a /F >nul 2>&1
            )
            echo 5010_service2 stopped
            