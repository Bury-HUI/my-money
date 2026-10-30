# -*- coding: utf-8 -*-
"""常驻监视《余额.xlsx》：一保存就自动导出 data.json 并推送到 GitHub。

由「余额自动同步」开机启动项在后台静默运行，日志写在 sync.log。
手动调试可以：python watch_sync.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "sync.log"
sys.path.insert(0, str(ROOT))
import sync_push  # noqa: E402


def log(text: str) -> None:
    line = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), text.rstrip())
    try:
        if LOG.exists() and LOG.stat().st_size > 200_000:
            LOG.write_text(line + "\n", encoding="utf-8")
        else:
            with LOG.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except OSError:
        pass


def once() -> bool:
    r = subprocess.run(
        [sys.executable, str(ROOT / "sync_push.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    ok = r.returncode == 0
    log(("[完成] " if ok else "[失败] ") + out.replace("\n", " | ")[:600])
    return ok


def main() -> None:
    book = sync_push.find_book()
    log("开始监视：%s" % book)
    last = book.stat().st_mtime
    pending_since = None

    while True:
        time.sleep(2)
        try:
            m = book.stat().st_mtime
        except FileNotFoundError:
            continue

        if m != last:
            last = m
            pending_since = time.time()
            log("检测到表格已保存，等待写入完成…")
            continue

        # 文件停止变化 3 秒后再同步，避开保存过程中的中间态
        if pending_since and time.time() - pending_since >= 3:
            pending_since = None
            once()


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        log("[退出] %s" % e)
    except Exception as e:  # noqa: BLE001
        log("[异常] %r" % e)
