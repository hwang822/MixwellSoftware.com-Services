@echo off

cd /d C:\Workarea\MixwellSoftware.com-Services\build

IF NOT EXIST MixwellSoftware.com-Services (
    echo Cloning repo first time...
    git clone https://github.com/hwang822/MixwellSoftware.com-Services
) ELSE (
    echo Updating repo...
    cd MixwellSoftware.com-Services
    git reset --hard
    git pull
)

echo Repo ready.