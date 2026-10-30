@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYW=D:\Python\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw"
start "" "%PYW%" "%~dp0watch_sync.py"
exit
