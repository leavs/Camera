# Camera 与公共 APT 软件源交接

更新日期：2026-10-26。此文档用于退出会话后继续维护，不包含任何密钥或令牌正文。

## 1. 当前状态

- 摄像头程序、桌面启动入口、DEB 打包、GitHub 自动构建、签名 APT 软件源均已完成。
- Camera 仓库：https://github.com/leavs/Camera （Public，主分支 `main`）。
- 公共软件源管理仓库：https://github.com/leavs/apt （Public，主分支 `main`）。
- 统一软件源与安装说明：https://leavs.github.io/apt/ 。以后新工具共用此入口。
- 旧源 https://leavs.github.io/Camera/ 继续发布 Camera，保留兼容；新客户端使用公共源。
- 当前设备安装版：`usb-camera-preview 1.0.0`。
- 最近已验证的线上包：`1.0.1+git2`，来自 Camera Release `apt-1.0.1+git2`。
- 当前设备尚未添加旧源或公共源到系统 APT 配置，因而不会自动更新到线上版本。
- 交接检查时预览程序未运行。点击左侧栏或桌面入口即可重新启动。
- 无待处理的已知构建失败。两个仓库最近检查的 Actions 均成功；公共源的计划任务会持续运行。

## 2. 本地目录及主要文件

Camera：`/home/ubuntu/Workspace/Codex/Camera`。

| 文件 | 用途 |
| --- | --- |
| `camera_preview.py` | PySide6 摄像头与窗口逻辑 |
| `start.sh` | 源码启动；创建虚拟环境、安装依赖、单实例锁 |
| `camera-icon.svg` | 应用图标 |
| `requirements.txt` / `requirements-build.txt` | 运行与打包依赖 |
| `build_deb.sh` | PyInstaller 构建并生成 DEB、SHA256 文件 |
| `packaging/launcher.sh` | 安装版 `/usr/bin/usb-camera-preview` 启动入口 |
| `packaging/usb-camera-preview.desktop` | 系统应用菜单入口 |
| `packaging/build_apt_repo.sh` | Camera 旧兼容源索引及签名 |
| `.github/workflows/apt.yml` | 云端构建、Release 和兼容源发布 |
| `VERSION` | 当前基础版本 `1.0.1` |

公共源：`/home/ubuntu/Workspace/Codex/apt`，详细说明见该仓库的 `README.md`、`HANDOVER.md`。

`build/`、`dist/`、`.venv/`、日志、Python 缓存不入 Git。当前本地安装包在 `dist/usb-camera-preview_1.0.0_amd64.deb`，约 55 MiB；它不是最新云端版本。

## 3. 程序行为与运行方式

- 当前系统：Ubuntu 24.04 amd64，GNOME Wayland；USB 设备名 `1080P USB Camera`，实际收到过 `1280×720` 视频帧。
- 窗口始终置顶，默认位于可用桌面区域右侧垂直居中，右侧留 12 像素边距。
- 顶部「⠿ 拖动」区域可拖动；拖动后调整大小保留位置；边界受桌面可用区域限制，避开任务栏。
- 右键可调整大小、切换显示器、重连摄像头或恢复右侧居中；Esc 或 ✕ 退出。
- 手动位置只在当前进程中保留，重新启动回到右侧居中。
- Linux 下有 DISPLAY 时默认使用 Qt xcb/XWayland，以支持精确定位。纯 Wayland 下定位可能受合成器限制。
- 只做本地视频预览，不录制或上传；无开机自启动配置。

安装版启动：

```bash
usb-camera-preview
```

源码启动：

```bash
cd /home/ubuntu/Workspace/Codex/Camera
bash start.sh
```

两个入口共用同一用户级 `flock` 锁，防止多个实例争用摄像头。已有实例时再次启动直接退出。

已安装文件：`/opt/usb-camera-preview/`、`/usr/bin/usb-camera-preview`、`/usr/share/applications/usb-camera-preview.desktop`。桌面及 `~/.local/share/applications/` 中的同名入口均已改为启动安装版，GNOME 左侧收藏已配置。

## 4. 打包与自动发布

本地构建：

```bash
cd /home/ubuntu/Workspace/Codex/Camera
bash build_deb.sh 1.0.2
sudo apt install ./dist/usb-camera-preview_1.0.2_amd64.deb
```

安装包内置 Python 与 Qt，约 200 MiB 安装体积，目标为 Ubuntu 24.04 amd64。其他 Debian/Ubuntu 版本未验证，不能宣称普遍兼容。系统库由 apt 安装。单纯 `bash start.sh` 不会刷新已安装版。

云端流程：

1. Camera 推送到 `main` 或手动触发 Actions。
2. Ubuntu 24.04 runner 构建、检查安装，版本为 `VERSION` 加 `+git<运行编号>`。
3. 上传 `deb-amd64` artifact，发布正式 GitHub Release（标签 `apt-<版本>`，含 DEB 与 SHA256）。
4. 并行更新 Camera 原 Pages 源。
5. 公共 `leavs/apt` 在每小时第 7、22、37、52 分钟检查全部登记项目的最新正式 Release，统一索引、签名、部署。

GitHub 计划任务可能延迟；紧急更新时，等待 Camera Release 成功后到 `leavs/apt` 的 Actions 手动运行。只提交到本地而未推送，不会触发云端打包。

正式发布时先修改 `VERSION`，再提交推送。构建依赖目前为版本范围，尚未做完全锁定或可复现构建。Actions 日志可能出现 Node.js 20 弃用提示，最近验证未阻止成功运行，后续可按官方说明升级 action 版本。

## 5. 签名与凭据

- 签名主密钥指纹：`AFA7 A554 83A3 A25D 6B1C EF37 9307 7871 3952 5089`。
- 公共源沿用原 Camera 签名密钥，密钥 UID 中仍有 Camera 字样；不影响共用签名验证。
- 两个仓库均配置 Actions secret `APT_SIGNING_KEY` 和变量 `APT_SIGNING_FINGERPRINT`。Camera 为保留旧源兼容仍需要签名；以后新工具只发布 Release，无需持有此私钥。
- 私钥本机备份目录：`/home/ubuntu/.local/share/usb-camera-preview/apt-signing/`，权限 700，包含 GnuPG 私钥及吊销证书。退出前或迁移设备时应另行安全备份；不要提交到 Git、Release 或 Pages。
- 公钥可公开：Camera 的 `packaging/apt-key.gpg`、公共源的 `keys/apt-key.gpg`。轮换密钥时须同步 Secrets、公钥、指纹、说明及客户端信任配置。
- GitHub CLI 已登录 `leavs`，凭据由系统 keyring 管理；不要在文档或日志中打印 token。设备迁移后可能需要重新登录。

## 6. 维护与验证

最近验证通过：真实 USB 视频、置顶属性、右侧居中坐标；拖动、缩放后位置保留、工作区边界和复位；DEB 真实安装与启动；重复启动保护；公共源 HTTPS 公钥一致性、APT 验签、候选版本解析、实际下载及校验和。

线上验证采用临时 APT 配置，不曾把源写入当前系统。需要自动更新时，按公共源网页的指纹核对及添加步骤操作，再运行 `sudo apt update && sudo apt install usb-camera-preview`。安装新版本前建议退出预览，更新后重新打开。

查询维护状态：

```bash
gh run list --repo leavs/Camera --limit 3
gh run list --repo leavs/apt --limit 3
gh release list --repo leavs/Camera
apt-cache policy usb-camera-preview
```

官方 Debian 包搜索及 Ubuntu 主归档 API 在本次会话查询均未发现同名包；不代表覆盖所有第三方源或未来状态。APT 按包名、优先级、版本选择来源，签名不把包绑定到作者。后续新工具建议使用 `leavs-` 前缀；当前 Camera 尚未更名，不能直接改包名而忽略升级迁移。

## 7. 公共源容量与下一步

Pages 1 GB 站点上限、100 GB/月软带宽为服务通用限制，并非仅 Free 账号；升级付费计划不会自动提高这两项。当前方案只保留各工具最新正式 Release 的包，历史包保留在 Releases；公共源在包总量超过 900 MB 时停止发布。规模增长时考虑迁移对象存储/CDN。

后续新工具的接入步骤见公共源交接文档：先配置工具自己的 DEB 构建及正式 Release，然后向公共源 `packages.json` 登记仓库和包名，手动发布并验证。

下次会话可直接说：**先阅读 Camera/HANDOVER.md 和 apt/HANDOVER.md，检查两个仓库 Git 与 Actions 状态，再继续维护。**

本次交接文档提交使用 `[skip ci]`，避免仅更新说明就额外构建 Camera 版本。公共源定时任务继续按计划运行。
