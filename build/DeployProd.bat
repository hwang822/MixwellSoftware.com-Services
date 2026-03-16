@echo off

cd /d %~dp0

setlocal EnableDelayedExpansion

set LOGFILE=deploy.log

del %LOGFILE% 2>nul

set STARTTIME=%DATE% %TIME%

set LOGFILE=deploy.log
set STARTTIME=%DATE% %TIME%

echo ===================================== >> %LOGFILE%
echo Build started: %STARTTIME% >> %LOGFILE%
echo ===================================== >> %LOGFILE%

echo Starting deployment...
echo.

REM -----------------------------
REM Project settings
REM -----------------------------

set REPO_URL=https://github.com/hwang822/MixwellSoftware.com-Services.git
set PROJECT_DIR=MixwellSoftware.com-Services
set PLATFORM_DIR=%PROJECT_DIR%\mixwell-platform
set SERVICES_DIR=%PLATFORM_DIR%\services
set PYTHON=%~dp0%PLATFORM_DIR%\venv\Scripts\python.exe

REM -----------------------------
REM Clone or update repo
REM -----------------------------

if not exist "%PROJECT_DIR%" (
    echo Cloning repository...
    echo Cloning repository... >> %LOGFILE%
    git clone %REPO_URL%
) else (
    echo Updating repository...
    echo Updating repository... >> %LOGFILE%
    cd %PROJECT_DIR%
    git pull
    cd ..
)

REM Copy .env file to build directory
SET SOURCE_ENV=..\mixwell-platform\.env
SET TARGET_ENV=%PROJECT_DIR%\.env
echo Copying .env file...
copy /Y "%SOURCE_ENV%" "%TARGET_ENV%"


REM -----------------------------
REM Start services
REM -----------------------------

echo.
echo Starting services...
echo Starting services... >> %LOGFILE%

FOR /D %%D IN (%SERVICES_DIR%\*) DO (
    call :StartService "%%~fD" "%%~nxD"
)

REM -----------------------------
REM Check portal
REM -----------------------------

timeout /t 3 >nul

powershell -Command ^
"try { (Invoke-WebRequest http://localhost:8000 -UseBasicParsing).StatusCode } catch { exit 1 }"

set ENDTIME=%DATE% %TIME%

echo Build finished: %ENDTIME% >> %LOGFILE%
echo ===================================== >> %LOGFILE%

echo Deployment finished.
REM pause
exit /b

REM -----------------------------
REM Start service
REM -----------------------------

:StartService

set SERVICE_PATH=%~1
set FOLDER_NAME=%~2

set PORT_PREFIX=%FOLDER_NAME:~0,4%
set PORT=%PORT_PREFIX:5=8%

set APP_FILE=%SERVICE_PATH%\app.py
echo SERVICE_PATH=%SERVICE_PATH% >> %LOGFILE%
echo FOLDER_NAME=%FOLDER_NAME% >> %LOGFILE%

echo To start APP_FILE !APP_FILE! >> %LOGFILE%

echo Starting %FOLDER_NAME% port %PORT%
echo Starting %FOLDER_NAME% port %PORT% >> %LOGFILE%

call :KillPort %PORT%

REM set CMD=start "" /B cmd /c "cd /d "!SERVICE_PATH!" && "%PYTHON%" app.py !PORT!"
start "" /B cmd /c "cd /d "!SERVICE_PATH!" && "%PYTHON%" app.py !PORT! >> !SERVICE_PATH!\service.log 2>&1"

echo CMD=!CMD! >> %LOGFILE%

!CMD!

if %ERRORLEVEL% EQU 0 (
    echo %FOLDER_NAME% OK >> %LOGFILE%
) else (
    echo %FOLDER_NAME% FAILED >> %LOGFILE%
)

exit /b

REM -----------------------------
REM Kill port
REM -----------------------------

:KillPort
set PORT=%1

FOR /F "tokens=5" %%a IN ('netstat -ano ^| findstr :%PORT%') DO (
    taskkill /PID %%a /F >nul 2>&1
)

exit /b

