@echo off
echo Starting the sequence...

echo --- Running git codes ---
CALL RepoStartup.bat

echo --- Running start app at 8000 ---
cd MixwellSoftware.com-Services\Portal
CALL AppStartup_8000.bat

echo --- Running start AI Service at 8001 ---
cd MixwellSoftware.com-Services\services\AIService
CALL AIServiceStartup-8001.bat

echo Sequence complete.
pause