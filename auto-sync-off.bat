@echo off
chcp 65001 >nul
echo 正在关闭后台自动同步…
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*watch_sync*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo 已关闭。重新开启请双击 auto-sync-on.bat。
timeout /t 3 >nul
exit
