# -*- coding: utf-8 -*-
"""安装「余额自动同步」开机启动项（把快捷方式放进当前用户的启动文件夹）。

重复运行无副作用。想关掉自动同步：删掉启动文件夹里的「余额自动同步.lnk」即可。
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYW = Path(sys.executable).with_name("pythonw.exe")
if not PYW.exists():
    PYW = Path(r"D:\Python\pythonw.exe")
SCRIPT = ROOT / "watch_sync.py"

STARTUP = Path(os.environ["APPDATA"]) / r"Microsoft\Windows\Start Menu\Programs\Startup"
LNK = STARTUP / "余额自动同步.lnk"
TMP = Path(os.environ["TEMP"]) / "wb_autostart.txt"

PS = r"""
$ErrorActionPreference = 'Stop'
$p = Get-Content -LiteralPath '%s' -Encoding UTF8
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut($p[2])
$lnk.TargetPath = $p[0]
$lnk.Arguments = '"' + $p[1] + '"'
$lnk.WorkingDirectory = $p[3]
$lnk.WindowStyle = 7
$lnk.Description = 'balance auto sync'
$lnk.Save()
Write-Output ('OK ' + $p[2])
""" % TMP


def main() -> int:
    for p in (PYW, SCRIPT, STARTUP):
        if not p.exists():
            print("缺失：", p)
            return 1

    TMP.write_text(
        "\n".join([str(PYW), str(SCRIPT), str(LNK), str(ROOT)]),
        encoding="utf-8",
    )
    r = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", PS],
        capture_output=True,
        text=True,
        errors="replace",
    )
    print((r.stdout or "").strip() or (r.stderr or "").strip())
    TMP.unlink(missing_ok=True)
    return 0 if LNK.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
