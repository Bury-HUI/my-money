@echo off
cd /d "%~dp0"
if not exist "watch.pid" goto nopid
set /p PIDV=<watch.pid
taskkill /F /PID %PIDV% >nul 2>&1
del /q "watch.pid" >nul 2>&1
echo [OK] auto sync stopped.
exit /b 0
:nopid
echo [SKIP] watch.pid not found - auto sync is probably not running.
exit /b 0
