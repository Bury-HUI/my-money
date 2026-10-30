# -*- coding: utf-8 -*-
"""可选：常驻监视《余额.xlsx》，一保存就自动导出并推送。

启动方式（不需要时直接关掉窗口即可）：
    python watch_sync.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import sync_push  # noqa: E402


def once() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "sync_push.py")],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    book = sync_push.find_book()
    print("监视中：", book)
    last = book.stat().st_mtime
    while True:
        time.sleep(3)
        try:
            m = book.stat().st_mtime
        except FileNotFoundError:
            continue
        if m != last:
            last = m
            time.sleep(2)          # 等表格保存完成
            once()
            print(time.strftime("%H:%M:%S"), "已同步")


if __name__ == "__main__":
    main()
