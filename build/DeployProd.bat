@echo off
cd /d %~dp0
setlocal EnableDelayedExpansion

REM =============================
REM Config
REM =============================
set BASE_DIR=%~dp0
set REPO_NAME=MixwellSoftware.com-Services
set PROJECT_DIR=%BASE_DIR%%REPO_NAME%
set PLATFORM_DIR=%PROJECT_DIR%\mixwell-platform
set LOGFILE=%BASE_DIR%deploy.log

set EXE_NAME=ms_trading_service.exe
set EXE_PATH=%PLATFORM_DIR%\dist\%EXE_NAME%

set REPO_URL=https://github.com/hwang822/MixwellSoftware.com-Services.git

REM =============================
REM Clean deploy.log
REM =============================
if exist "%LOGFILE%" del /f /q "%LOGFILE%" 2>nul

echo ===================================== > "%LOGFILE%"
echo CLEAN DEPLOY START: %DATE% %TIME% >> "%LOGFILE%"
echo ===================================== >> "%LOGFILE%"

echo.
echo =====================================
echo CLEAN DEPLOY START
echo =====================================
echo.

REM =============================
REM Stop Existing EXE
REM =============================
echo Stopping old %EXE_NAME% ...
echo Stopping old %EXE_NAME% ... >> "%LOGFILE%"

taskkill /F /IM %EXE_NAME% /T >> "%LOGFILE%" 2>&1

timeout /t 3 >nul

REM =============================
REM Git Clone / Pull
REM =============================
if not exist "%PROJECT_DIR%" (

    echo Cloning repository...
    echo Cloning repository... >> "%LOGFILE%"

    git clone %REPO_URL% >> "%LOGFILE%" 2>&1

    if errorlevel 1 (
        echo ERROR: Git clone failed
        echo ERROR: Git clone failed >> "%LOGFILE%"
        goto FAIL
    )

) else (

    echo Updating repository...
    echo Updating repository... >> "%LOGFILE%"

    pushd "%PROJECT_DIR%"

    git pull >> "%LOGFILE%" 2>&1

    if errorlevel 1 (
        echo ERROR: Git pull failed
        echo ERROR: Git pull failed >> "%LOGFILE%"
        popd
        goto FAIL
    )

    popd
)

REM =============================
REM Python venv setup
REM =============================
if not exist "%PLATFORM_DIR%\venv" (

    echo Creating virtual environment...
    echo Creating virtual environment... >> "%LOGFILE%"

    python -m venv "%PLATFORM_DIR%\venv" >> "%LOGFILE%" 2>&1
)

set PYTHON=%PLATFORM_DIR%\venv\Scripts\python.exe
set PIP=%PLATFORM_DIR%\venv\Scripts\pip.exe

REM =============================
REM Install Dependencies
REM =============================
echo Installing dependencies...
echo Installing dependencies... >> "%LOGFILE%"

%PIP% install -r "%PLATFORM_DIR%\requirements.txt" >> "%LOGFILE%" 2>&1

if errorlevel 1 (
    echo ERROR: pip install failed
    echo ERROR: pip install failed >> "%LOGFILE%"
    goto FAIL
)

REM =============================
REM Install PyInstaller
REM =============================
echo Installing PyInstaller...
echo Installing PyInstaller... >> "%LOGFILE%"

%PIP% install pyinstaller >> "%LOGFILE%" 2>&1

REM =============================
REM Copy .env
REM =============================
SET SOURCE_ENV=..\mixwell-platform\.env
SET TARGET_ENV=%PLATFORM_DIR%\.env

echo Copying .env file...
echo Copying .env file... >> "%LOGFILE%"

copy /Y "%SOURCE_ENV%" "%TARGET_ENV%" >> "%LOGFILE%" 2>&1

REM =============================
REM Build EXE
REM =============================
echo Building %EXE_NAME% ...
echo Building %EXE_NAME% ... >> "%LOGFILE%"

cd /d "%PLATFORM_DIR%\portal"

%PYTHON% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --name ms_trading_service ^
    --distpath "%PLATFORM_DIR%\dist" ^
    --workpath "%PLATFORM_DIR%\build" ^
    --specpath "%PLATFORM_DIR%\build" ^
    --noconsole ^
    app.py >> "%LOGFILE%" 2>&1

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    echo ERROR: PyInstaller build failed >> "%LOGFILE%"
    goto FAIL
)

REM =============================
REM Launch EXE
REM =============================
echo Starting %EXE_NAME% ...
echo Starting %EXE_NAME% ... >> "%LOGFILE%"

start "MS-TRADING-SERVICE" "%EXE_PATH%"

timeout /t 8 >nul

REM =============================
REM Health Check
REM =============================
echo Checking portal health...
echo Checking portal health... >> "%LOGFILE%"

powershell -Command ^
"try { ^
    $r = Invoke-WebRequest http://localhost:8000 -UseBasicParsing; ^
    if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } ^
} catch { exit 1 }"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Portal not responding
    echo ERROR: Portal not responding >> "%LOGFILE%"
    goto FAIL
)

REM =============================
REM SUCCESS
REM =============================
echo.
echo =====================================
echo DEPLOY SUCCESS
echo =====================================

echo DEPLOY SUCCESS >> "%LOGFILE%"
echo Build finished: %DATE% %TIME% >> "%LOGFILE%"

pause
exit /b 0

REM =============================
REM FAIL
REM =============================
:FAIL

echo.
echo =====================================
echo DEPLOY FAILED
echo =====================================

echo DEPLOY FAILED >> "%LOGFILE%"
echo Build failed: %DATE% %TIME% >> "%LOGFILE%"

pause
exit /b 1