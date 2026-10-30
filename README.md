# 余额台账（GitHub Pages）

免登录直接打开余额：https://bury-hui.github.io/my-money/

## 数据链路

```
余额.xlsx  --sync_push.py-->  data.json  --git push-->  GitHub Pages  --fetch-->  网页
```

## 改完表格后怎么更新

双击 `sync-push.bat`（会导出 data.json 并推送到 GitHub）。
推送成功后等 30~60 秒，网页右上角点 ⟳ 强制刷新即可。

也可以命令行：

```
python sync_push.py            # 导出 + 推送
python sync_push.py --no-push  # 只导出，不推送
```

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `sync_push.py` | 读《余额.xlsx》→ 生成 `data.json` → 提交并推送（自包含，不依赖外部脚本）|
| `sync-push.bat` | 一键版：双击即可 |
| `watch_sync.py` | 可选：常驻监视表格，一保存就自动推送（`python watch_sync.py`）|
| `data.json` | 网页数据源，由脚本生成，不要手改 |
| `token.txt` | 可选。如果哪天推送要求登录，把 GitHub classic PAT 粘进来即可（已被 .gitignore 忽略）|

## 表格位置

脚本会自动在以下位置找《余额.xlsx》：
`仓库同级的上级目录` → `仓库目录` → `桌面` → `E:\AAA-DeskBox\我的桌面\余额`。
如果放在别处，把完整路径写进 `xlsx_path.txt` 即可。
