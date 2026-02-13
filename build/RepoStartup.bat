@echo off
git init
rmdir MixwellSoftware.com-Services
git clone https://github.com/hwang822/MixwellSoftware.com-Services

cd portal
python app.py