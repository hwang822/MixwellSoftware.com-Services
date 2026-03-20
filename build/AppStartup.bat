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

REM -----------------------------
REM Project settings
REM -----------------------------

set REPO_URL=https://github.com/hwang822/MixwellSoftware.com-Services.git
set PROJECT_DIR=MixwellSoftware.com-Services
set PLATFORM_DIR=%PROJECT_DIR%\mixwell-platform
set SERVICES_DIR=%PLATFORM_DIR%\services
set PYTHON=%PLATFORM_DIR%\venv\Scripts\python.exe

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

%PYTHON% %PLATFORM_DIR%\portal\app.py 8000


pause