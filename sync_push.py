# -*- coding: utf-8 -*-
"""把《余额.xlsx》导出成 data-<年份>.json 并推送到 GitHub Pages。

每年一张工作表（表名 = 年份，如 2026、2027），每年一个数据文件，
网页上可以切换年份。data.json 始终指向当年，兼容旧链接。

自包含版本：不再依赖外部 server.py，直接在仓库目录里运行即可。
    python sync_push.py            # 导出 + 推送
    python sync_push.py --no-push  # 只导出，不推送
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent            # .../my-money
BRANCH = "main"
BOOK = "余额.xlsx"

# pythonw / 重定向环境下 stdout 编码不稳，统一按 UTF-8 输出，坏字符用替换兜底
for _s in (sys.stdout, sys.stderr):
    if _s is not None:
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

# 可能的表格位置（按优先级）
CANDIDATES = [
    ROOT.parent / BOOK,                            # 仓库旁边（推荐布局）
    ROOT / BOOK,
    Path.home() / "Desktop" / BOOK,
    Path("E:/AAA-DeskBox/我的桌面/余额") / BOOK,
    Path("C:/Users/33431/Desktop") / BOOK,
]


# ---------------------------------------------------------------- 找表格
def find_book() -> Path:
    override = ROOT / "xlsx_path.txt"
    if override.exists():
        p = Path(override.read_text(encoding="utf-8").strip())
        if p.exists():
            return p
    for p in CANDIDATES:
        if p.exists():
            return p
    hits = sorted(
        (p for p in Path.home().rglob(BOOK) if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if hits:
        return hits[0]
    raise SystemExit("找不到《余额.xlsx》，请把表格放到 %s 旁边" % ROOT.parent)


# ---------------------------------------------------------------- 读表格
def ensure_openpyxl():
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("正在安装 openpyxl …")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "openpyxl"], check=False)


def sheet_year(name: str):
    """表名是四位数字才算年份表。"""
    n = str(name).strip()
    return int(n) if n.isdigit() and len(n) == 4 else None


def date_text(v) -> str:
    if isinstance(v, (dt.datetime, dt.date)):
        return "%d.%d" % (v.month, v.day)
    return str(v).strip()


def num(v):
    if v is None or v == "":
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def build_payload(path: Path):
    """读表格。刚保存时文件可能被 WPS/Excel 短暂占用，失败自动重试。"""
    last = None
    for i in range(6):
        try:
            return _build_payload(path)
        except (PermissionError, OSError, zipfile.BadZipFile) as e:
            last = e
            time.sleep(2)
    raise SystemExit("读取表格失败（可能正在被 WPS/Excel 占用）：%s" % last)


def _build_payload(path: Path) -> dict:
    """返回 {年份: payload}。只导出：有数据的年份表 + 今年（哪怕还没填）。"""
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    this_year = dt.date.today().year
    payloads = {}

    for name in wb.sheetnames:
        year = sheet_year(name)
        if year is None:
            continue
        ws = wb[name]

        header = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
        header = [str(h).strip() if h is not None else "" for h in header]
        account_keys = [h for h in header[1:-2] if h]

        rows = []
        prev_total = None  # 上一条已填写的记录的总额，用于兜底计算「消费」
        for r in range(2, ws.max_row + 1):
            raw_date = ws.cell(r, 1).value
            if raw_date is None or str(raw_date).strip() == "":
                continue
            accounts = {key: num(ws.cell(r, 2 + i).value) for i, key in enumerate(account_keys)}
            total = num(ws.cell(r, 2 + len(account_keys)).value)
            spend = num(ws.cell(r, 3 + len(account_keys)).value)

            empty = all(v is None for v in accounts.values())
            if empty:
                total = None
                spend = None
            else:
                if total is None:  # 公式还没被 WPS/Excel 重算过时，按各账户之和兜底
                    total = round(sum(v for v in accounts.values() if v is not None), 2)
                if spend is None and prev_total is not None:  # 消费 = 上次总额 - 本次总额
                    spend = round(prev_total - total, 2)

            rows.append(
                {
                    "row": r,
                    "date": date_text(raw_date),
                    "accounts": accounts,
                    "total": total,
                    "empty": empty,
                    "spend": spend,
                }
            )
            if not empty:
                prev_total = total

        filled = [x for x in rows if not x["empty"]]
        if not filled and year < this_year:
            continue  # 过去的空年份表不导出；今年和未来年份即使没填也导出（网页能切过去看）
        if filled:
            latest = filled[-1]
            week = [x["spend"] for x in filled[-7:] if x["spend"] is not None]
            summary = {
                "latest_date": latest["date"],
                "latest_row": latest["row"],
                "total": latest["total"],
                "accounts": latest["accounts"],
                "week_spend": round(sum(week), 2) if week else 0,
                "filled_count": len(filled),
                "row_count": len(rows),
            }
        else:
            summary = {
                "latest_date": None,
                "latest_row": None,
                "total": None,
                "accounts": {},
                "week_spend": None,
                "filled_count": 0,
                "row_count": len(rows),
            }
        summary.update({"sheet": name, "year": year})

        payloads[year] = {
            "headers": header,
            "account_keys": account_keys,
            "rows": rows,
            "summary": summary,
        }

    if not payloads:
        raise SystemExit("表格里没有可导出的年份工作表（表名需为 2026、2027 这样的四位数）")
    return payloads


# ---------------------------------------------------------------- 导出
def core(payload: dict) -> str:
    """去掉时间戳后的指纹，用来判断数据到底有没有变。"""
    s = {k: v for k, v in payload["summary"].items() if k != "generated_at"}
    return json.dumps(
        {"rows": payload["rows"], "summary": s, "account_keys": payload["account_keys"]},
        ensure_ascii=False,
        sort_keys=True,
    )


def _write_if_changed(fname: str, payload: dict) -> bool:
    """内容有变才写文件，避免无意义的提交。返回是否真的写了。"""
    out = ROOT / fname
    if out.exists():
        try:
            if core(json.loads(out.read_text(encoding="utf-8"))) == core(payload):
                return False
        except (json.JSONDecodeError, KeyError):
            pass
    payload["summary"]["generated_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def export(book: Path) -> tuple[bool, str]:
    payloads = build_payload(book)
    this_year = dt.date.today().year
    years = sorted(payloads.keys(), reverse=True)
    current = this_year if this_year in payloads else years[0]

    changed = []
    for y in years:
        if _write_if_changed("data-%d.json" % y, payloads[y]):
            changed.append(y)
    (ROOT / "years.json").write_text(
        json.dumps({"years": years, "current": current}, ensure_ascii=False),
        encoding="utf-8",
    )
    # data.json = 当年数据，兼容旧链接
    if _write_if_changed("data.json", payloads[current]):
        changed.append("data.json")

    s = payloads[current]["summary"]
    if s["filled_count"]:
        line = "当年 [%s] 最新 %s / %s 元" % (s["sheet"], s["latest_date"], s["total"])
    else:
        line = "当年 [%s] 还没有记录" % s["sheet"]
    if changed:
        print("表格：%s" % book)
        print("导出更新：%s（%s）" % (", ".join(map(str, changed)), line))
    else:
        print("数据没有变化（%s）。" % line)
    latest = payloads[max(years)]["summary"]
    msg = latest["latest_date"] if latest["filled_count"] else str(max(years))
    return bool(changed), msg


# ---------------------------------------------------------------- 推送
def run_git(args, **kw):
    return subprocess.run(
        ["git", "-c", "user.name=Bury-HUI",
         "-c", "user.email=Bury-HUI@users.noreply.github.com"] + args,
        cwd=str(ROOT), text=True, **kw,
    )


def push(changed: bool, msg_date: str) -> bool:
    run_git(["add", "-A"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    staged = run_git(["diff", "--cached", "--quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if staged.returncode == 0:
        print("没有需要提交的改动。")
        return True

    msg = "update balance data %s" % msg_date
    commit = run_git(["commit", "-m", msg], capture_output=True)
    if commit.returncode != 0:
        print("提交失败：", (commit.stderr or "").strip()[:300])
        return False
    print("提交：", msg)

    current = run_git(["branch", "--show-current"], capture_output=True).stdout.strip()
    if current != BRANCH:
        run_git(["branch", "-M", BRANCH], capture_output=True)

    token_file = ROOT / "token.txt"
    token = token_file.read_text(encoding="utf-8").strip() if token_file.exists() else ""
    if token:
        url = "https://Bury-HUI:%s@github.com/Bury-HUI/my-money.git" % token
        r = run_git(["push", url, "HEAD:" + BRANCH], capture_output=True)
    else:
        r = run_git(["push", "-u", "origin", BRANCH], capture_output=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        print("推送失败：")
        print(err[:800])
        print("\n如果提示需要凭据：把 GitHub classic PAT 粘到 %s 后重跑本脚本。" % (ROOT / "token.txt"))
        return False

    print("推送成功 → https://bury-hui.github.io/my-money/")
    print("（GitHub Pages 一般 30~60 秒后生效，网页点右上角 ⟳ 可强制刷新）")
    return True


def main() -> int:
    ensure_openpyxl()
    book = find_book()
    changed, msg_date = export(book)
    if "--no-push" in sys.argv:
        return 0
    return 0 if push(changed, msg_date) else 1


if __name__ == "__main__":
    raise SystemExit(main())
