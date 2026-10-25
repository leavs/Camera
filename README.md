# USB 摄像头实时预览

本地 Python / PySide6 桌面程序，默认优先打开 USB 摄像头，保持窗口置顶，固定在启动时鼠标所在屏幕的右侧，按桌面可用区域垂直居中。避开任务栏及顶部栏，距可用区域右侧保留 12 像素间距。

## 启动

当前设备已安装「USB 摄像头预览」桌面图标并固定到 GNOME 左侧栏，点击左侧栏图标或双击桌面图标即可启动。重复启动会避免打开多个摄像头窗口。

在本目录运行：

```bash
bash start.sh
```

首次运行会在 `.venv` 中安装 `requirements.txt` 的依赖。需要 Python 3.10+、venv 和图形桌面。Ubuntu 若缺少 Qt X11 运行库，可安装 `libxcb-cursor0`。

## 操作

- 顶部下拉框选择摄像头，USB 设备插拔时自动刷新。
- 按住顶部「⠿ 拖动」区域可移动窗口，移动范围限制在桌面可用区域内，避免覆盖任务栏。拖动后调整大小保留当前位置；右键选择「恢复右侧居中」可复位。重新启动默认回到右侧居中。
- 右键窗口可选择 320、384 或 640 像素宽度、切换显示器、重新连接摄像头。
- 点击 ✕ 或按 Esc 退出并释放摄像头。
- 画面保持原始比例，仅本地预览，不录制或上传。

在 Linux 的 GNOME Wayland 桌面下，程序默认使用 XWayland，以支持窗口定位与置顶。手动设置 `QT_QPA_PLATFORM=wayland` 后，位置可能受桌面合成器限制。自动隐藏任务栏的避让取决于桌面报告的可用区域。

## APT 软件源

公开的软件源：`https://leavs.github.io/Camera/`。当前提供 Ubuntu 24.04 amd64 安装包，其他发行版未验证；不是面向所有 Debian/Ubuntu 版本的通用包。

首次添加软件源：

```bash
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL https://leavs.github.io/Camera/apt-key.gpg -o /tmp/camera-apt-key.gpg
gpg --show-keys --with-fingerprint /tmp/camera-apt-key.gpg
```

核对主密钥指纹为 `AFA7 A554 83A3 A25D 6B1C EF37 9307 7871 3952 5089`，然后执行：

```bash
sudo install -d -m 755 /etc/apt/keyrings
sudo install -m 644 /tmp/camera-apt-key.gpg /etc/apt/keyrings/leavs-camera.gpg
echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/leavs-camera.gpg] https://leavs.github.io/Camera/ stable main' | sudo tee /etc/apt/sources.list.d/leavs-camera.list
sudo apt update
sudo apt install usb-camera-preview
```

之后使用 `sudo apt update && sudo apt upgrade` 获取更新。

每次推送到 `main` 或手动触发 Actions，会在 Ubuntu 24.04 上构建安装包、检查安装、生成 APT 索引、签名并部署至 Pages。版本为 `VERSION` 加 `+git<运行编号>`，例如 `1.0.1+git1`。Pages 保留最近一次成功发布的软件包，构建产物也会保存在 Actions 的 `deb-amd64` artifact 中。

公钥和指纹位于 `packaging/apt-key.gpg`、`packaging/apt-key.fingerprint`；私钥只存储于 GitHub Actions secret `APT_SIGNING_KEY`，本机备份位于 `~/.local/share/usb-camera-preview/apt-signing/`，不会提交至仓库。仓库变量 `APT_SIGNING_FINGERPRINT` 指定签名密钥。密钥变更后应更新公钥、指纹和客户端信任配置。

## DEB 安装包

面向 Ubuntu 24.04 amd64，内置 Python、PySide6 和 Qt，无需在目标设备上安装 pip 依赖或创建虚拟环境。系统依赖由 apt 安装。

```bash
sudo apt install ./dist/usb-camera-preview_1.0.0_amd64.deb
```

安装后可从应用菜单打开「USB 摄像头预览」，或运行 `usb-camera-preview`。桌面图标及左侧栏收藏属于用户设置，安装包不会自动修改。卸载命令为 `sudo apt remove usb-camera-preview`。

重新构建（需联网安装构建依赖）：

```bash
bash build_deb.sh 1.0.0
```

产物及 SHA256 校验文件保存在 `dist/`。如需支持较旧系统，应在对应系统中重新构建。

## 当前设备验证

已在 Ubuntu 24.04 / GNOME 桌面检测到 `1080P USB Camera`，并收到实际 `1280×720` 视频帧。默认窗口尺寸为 `384×292`；系统工作区域为 `(66, 32, 1854, 1048)` 时，右侧居中坐标为 `(1524, 410)`。已通过 X11 窗口属性确认置顶状态，Python 语法与启动脚本语法检查通过。
