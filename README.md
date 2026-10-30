# 余额台账（GitHub Pages）

免登录直接打开余额：https://bury-hui.github.io/my-money/

## 数据链路

```
余额.xlsx --(保存)--> watch_sync.py --> data.json --> git push --> GitHub Pages --> 网页
```

## 日常使用：什么都不用做

表格一保存，后台的 `watch_sync.py` 会在 5 秒内自动导出并推送，网页 30~60 秒后刷新即是最新。

- 开机自动启动（启动文件夹里的「余额自动同步」快捷方式）
- 后台静默运行，没有窗口；日志在 `sync.log`
- 手动兜底：双击 `sync-push.bat`（导出 + 推送，带可见窗口）

## 常用命令

| 想做的事 | 操作 |
| --- | --- |
| 立即开启自动同步（不用重启） | 双击 `auto-sync-on.bat` |
| 临时关闭自动同步 | 双击 `auto-sync-off.bat`，或删掉启动文件夹里的「余额自动同步.lnk」 |
| 只导出不推送 | `python sync_push.py --no-push` |
| 重新安装开机启动项 | `python setup_autostart.py` |

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `sync_push.py` | 读《余额.xlsx》→ 生成 `data.json` → 提交并推送（自包含，不依赖外部脚本）|
| `watch_sync.py` | 常驻监视表格，一保存就自动推送（单实例运行）|
| `sync-push.bat` | 手动一键同步（导出 + 推送）|
| `auto-sync-on.bat` / `auto-sync-off.bat` | 开启 / 关闭后台自动同步 |
| `setup_autostart.py` | 把开机启动项装到当前用户的启动文件夹 |
| `data.json` | 网页数据源，由脚本生成，不要手改 |
| `token.txt` | 可选。哪天推送要求登录，把 GitHub classic PAT 粘进来即可（已被 .gitignore 忽略）|

## 表格位置

脚本会自动找《余额.xlsx》：`仓库上级目录` → `仓库目录` → `桌面` → `E:\AAA-DeskBox\我的桌面\余额`。
放在别处就把完整路径写进 `xlsx_path.txt`。
