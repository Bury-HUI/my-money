@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
if exist "D:\Python\python.exe" set "PY=D:\Python\python.exe"
if not defined PY set "PY=python"
echo ==========================================
echo   sync 余额.xlsx  ->  data.json  ->  GitHub
echo ==========================================
"%PY%" "%~dp0sync_push.py" %*
echo.
if errorlevel 1 (
  echo [FAILED] see error above.
) else (
  echo [OK] open https://bury-hui.github.io/my-money/ and click the refresh icon.
)
echo.
pause
