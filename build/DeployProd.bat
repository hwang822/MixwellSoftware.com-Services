@echo off
cd /d %~dp0
setlocal EnableDelayedExpansion

REM =============================
REM Config
REM =============================
set BASE_DIR=%~dp0
set PROJECT_DIR=%BASE_DIR%MixwellSoftware.com-Services
set PLATFORM_DIR=%PROJECT_DIR%\mixwell-platform
set SERVICES_DIR=%PLATFORM_DIR%\services
set LOGFILE=%BASE_DIR%deploy.log
set PORTAL_PORT=8000

REM 清空日志
del %LOGFILE% 2>nul

echo ===================================== >> %LOGFILE%
echo Build started: %DATE% %TIME% >> %LOGFILE%
echo ===================================== >> %LOGFILE%

echo Starting deployment...
echo.

REM =============================
REM Git Clone / Pull
REM =============================
if not exist "%PROJECT_DIR%" (
    echo Cloning repository...
    echo Cloning repository... >> %LOGFILE%
    git clone https://github.com/hwang822/MixwellSoftware.com-Services.git
) else (
    echo Updating repository...
    echo Updating repository... >> %LOGFILE%
    pushd "%PROJECT_DIR%"
    git pull
    popd
)

REM =============================
REM Python venv setup
REM =============================

set PYTHON=%PLATFORM_DIR%\venv\Scripts\python.exe

REM Check if venv python exists and works
if exist "%PYTHON%" (
    "%PYTHON%" --version >nul 2>&1
)

REM If broken or missing, recreate venv
if errorlevel 1 (
    echo Broken venv detected. Recreating...
    echo Broken venv detected. Recreating... >> %LOGFILE%

    rmdir /s /q "%PLATFORM_DIR%\venv"

    py -3.12 -m venv "%PLATFORM_DIR%\venv"

    "%PLATFORM_DIR%\venv\Scripts\pip.exe" install -r "%PLATFORM_DIR%\requirements.txt"
)

REM If venv does not exist at all
if not exist "%PYTHON%" (
    echo Creating virtual environment...
    echo Creating virtual environment... >> %LOGFILE%

    py -3.12 -m venv "%PLATFORM_DIR%\venv"

    "%PLATFORM_DIR%\venv\Scripts\pip.exe" install -r "%PLATFORM_DIR%\requirements.txt"
)

set PYTHON=%PLATFORM_DIR%\venv\Scripts\python.exe"

REM echo Installing dependencies...
REM echo Installing dependencies... >> %LOGFILE%
REM "%PLATFORM_DIR%\venv\Scripts\pip.exe" install -r "%PLATFORM_DIR%\requirements.txt"
REM %PLATFORM_DIR%\venv\Scripts

REM Copy .env file to build directory
SET SOURCE_ENV=..\mixwell-platform\.env
SET TARGET_ENV=%PLATFORM_DIR%\.env
echo Copying .env file...
copy /Y "%SOURCE_ENV%" "%TARGET_ENV%"  >> %LOGFILE%

set PYTHON=%PLATFORM_DIR%\venv\Scripts\python.exe

REM =============================
REM Start Services
REM =============================
echo.
echo Starting services...
echo Starting services... >> %LOGFILE%

call :KillPort %PORTAL_PORT%  >> %LOGFILE% 
%PYTHON% %PLATFORM_DIR%\portal\app.py %PORTAL_PORT% >> %LOGFILE%

REM for /D %%D in ("%SERVICES_DIR%\*") do (
REM     call :StartService "%%~fD" "%%~nxD"
REM )

REM =============================
REM Check Portal
REM =============================
timeout /t 3 >nul

powershell -Command ^
"try { (Invoke-WebRequest http://localhost:8000 -UseBasicParsing).StatusCode } catch { exit 1 }"

if %ERRORLEVEL% EQU 0 (
    echo Portal OK >> %LOGFILE%
    echo Portal started successfully
) else (
    echo Portal FAILED >> %LOGFILE%
    echo ERROR: Portal not responding
)

echo ===================================== >> %LOGFILE%
echo Build finished: %DATE% %TIME% >> %LOGFILE%

echo Deployment finished.
pause
exit /b

REM =============================
REM Kill Port
REM =============================
:KillPort
set PORT=%1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT%') do (
    taskkill /PID %%a /F >nul 2>&1
)

exit /b