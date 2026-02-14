@echo off

echo Starting deployment...

echo --- Git Sync ---
CALL RepoStartup.bat

echo --- Kill old ports ---
SET ROOT_PATH=C:\Workarea\MixwellSoftware.com-Services\build\MixwellSoftware.com-Services
SET PORTAL_PORT=8000
SET AI_SERVICE_PORT=8001
SET CMD_SERVICE_PORT=8002
SET VIDEO_SERVICE_PORT=8003
SET EMAIL_SERVICE_PORT=8004
SET TRAVEL_SERVICE_PORT=8005
SET DATAAPI_SERVICE_PORT=8006
SET RDP_SERVICE_PORT=8007


CALL :KillPort %PORTAL_PORT%
CALL :KillPort %AI_SERVICE_PORT%
CALL :KillPort %CMD_SERVICE_PORT%
CALL :KillPort %DATAAPI_SERVICE_PORT%
CALL :KillPort %EMAIL_SERVICE_PORT%
CALL :KillPort %RDP_SERVICE_PORT%
CALL :KillPort %TRAVEL_SERVICE_PORT%
CALL :KillPort %VIDEO_SERVICE_PORT%

echo --- Start Portal ---
start /B "" cmd /c "cd /d %ROOT_PATH%\portal && python app.py %PORTAL_PORT%"

timeout /t 3 >nul

echo --- Start AI Service 8001 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\services\AIService && python aiService.py %AI_SERVICE_PORT%"

echo --- Start Cam Service 8002 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\services\CAMService && python camService.py %CMD_SERVICE_PORT%"

echo --- Start Video Service 8003 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\services\VideoService && python videoService.py %VIDEO_SERVICE_PORT%"

echo --- Start Email Service 8004 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\services\EmailService && python emailService.py %EMAIL_SERVICE_PORT%"

echo --- Start Travel Service 8005 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\services\TravelService && python travelService.py %TRAVEL_SERVICE_PORT%"

echo --- Start Data API Service 8006 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\services\DataAPIService && python dataAPIService.py %DATAAPI_SERVICE_PORT%"

echo --- Start RDP Service 8007 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\services\RDPService && python rdpService.py %RDP_SERVICE_PORT%"

echo Deployment Complete
pause
exit /b

:KillPort
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%1') do taskkill /F /PID %%a >nul 2>&1
exit /b