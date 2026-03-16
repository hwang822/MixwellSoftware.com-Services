@echo off

echo Starting deployment...

echo --- Git Sync ---
CALL RepoStartup.bat

echo --- Kill old ports ---

SET PORTAL_PORT=8000
SET AI_SERVICE_PORT=8001
SET CAM_SERVICE_PORT=8002
SET DATA_SERVICE_PORT=8003
SET EMAIL_SERVICE_PORT=8004
SET RDP_SERVICE_PORT=8005
SET REGISTRY_SERVICE_PORT=8006
SET USER_SERVICE_PORT=8007
SET VIDEO_SERVICE_PORT=8008
SET SERVICE1_SERVICE_PORT=8009
SET SERVICE2_SERVICE_PORT=8010

CALL :KillPort %PORTAL_PORT%
CALL :KillPort %AI_SERVICE_PORT%
CALL :KillPort %CAM_SERVICE_PORT%
CALL :KillPort %DATA_SERVICE_PORT%
CALL :KillPort %EMAIL_SERVICE_PORT%
CALL :KillPort %RDP_SERVICE_PORT%
CALL :KillPort %REGISTRY_SERVICE_PORT%
CALL :KillPort %USER_SERVICE_PORT%
CALL :KillPort %VIDEO_SERVICE_PORT%
CALL :KillPort %SERVICE1_SERVICE_PORT%
CALL :KillPort %SERVICE2_SERVICE_PORT%

timeout /t 3 >nul

SET PYTHON_PATH=C:\Workarea\MixwellSoftware.com-Services\build\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts
SET ROOT_PATH=C:\Workarea\MixwellSoftware.com-Services\build\MixwellSoftware.com-Services\mixwell-platform\services

echo --- Start Portal Service 8000 ---
start "" cmd /c "cd /d %ROOT_PATH%\5000_portal && %PYTHON_PATH%\python app.py %PORTAL_PORT%"

echo --- Start AI Service 8001 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5001_ai && %PYTHON_PATH%\python app.py %AI_SERVICE_PORT%"

echo --- Start Cam Service 8002 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5002_cam && %PYTHON_PATH%\python app.py %CAM_SERVICE_PORT%"

echo --- Start Data Service 8003 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5003_data && %PYTHON_PATH%\python app.py %DATA_SERVICE_PORT%"

echo --- Start Email Service 8004 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5004_email && %PYTHON_PATH%\python app.py %EMAIL_SERVICE_PORT%"

echo --- Start rdb Service 8005 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5005_rdp && %PYTHON_PATH%\python app.py %RDP_SERVICE_PORT%"

echo --- Start Registry Service 8006 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5006_registry && %PYTHON_PATH%\python app.py %REGISTRY_SERVICE_PORT%"

echo --- Start user Service 8007 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5007_user && %PYTHON_PATH%\python app.py %USER_SERVICE_PORT%"

echo --- Start video Service 8008 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5008_video && %PYTHON_PATH%\python app.py %VIDEO_SERVICE_PORT%"

echo --- Start service1 Service 8009 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5009_service1 && %PYTHON_PATH%\python app.py %SERVICE1_SERVICE_PORT%"

echo --- Start service2 Service 8010 ---
start /B "" cmd /c "cd /d %ROOT_PATH%\5010_service2 && %PYTHON_PATH%\python app.py %SERVICE2_SERVICE_PORT%"


echo Deployment Complete
pause
exit /b

:KillPort
SET PORT=%1
FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :%PORT%') DO (
    echo Killing PID %%a on port %PORT%
    taskkill /PID %%a /F
)
exit /b