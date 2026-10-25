"""Local USB camera preview pinned inside the desktop work area."""
import os
import sys

# XWayland allows desktop positioning on GNOME Wayland.
if sys.platform.startswith("linux") and os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QAction, QCursor, QGuiApplication
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget


class DragHandle(QLabel):
    def __init__(self, preview):
        super().__init__("⠿ 拖动", preview)
        self.preview = preview
        self.offset = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("按住鼠标左键拖动窗口")
        self.setMinimumWidth(60)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.preview.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            cursor = event.globalPosition().toPoint()
            screen = QGuiApplication.screenAt(cursor) or self.preview.anchor_screen
            self.preview.anchor_screen = screen
            self.preview.manually_positioned = True
            self.preview.move_within_screen(cursor - self.offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB 摄像头预览")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("QWidget {background:#171b24;color:#edf2fa;} QPushButton,QComboBox {background:#303849;border:0;padding:5px;border-radius:4px;}")
        self.camera = None
        self.selected_id = None
        self.target_width = 384
        self.manually_positioned = False
        self.frames = 0
        self.session = QMediaCaptureSession(self)
        self.devices = QMediaDevices(self)
        self.devices.videoInputsChanged.connect(self.refresh_devices)
        self.video = QVideoWidget(self)
        self.video.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.session.setVideoOutput(self.video)
        self.video.videoSink().videoFrameChanged.connect(self.frame_received)
        self.selector = QComboBox()
        self.selector.setMinimumWidth(80)
        self.selector.currentIndexChanged.connect(self.select_camera)
        close = QPushButton("✕")
        close.setToolTip("关闭摄像头并退出（Esc）")
        close.clicked.connect(self.close)
        bar = QHBoxLayout()
        self.drag_handle = DragHandle(self)
        bar.addWidget(self.drag_handle)
        bar.addWidget(self.selector, 1)
        bar.addWidget(close)
        self.status = QLabel("正在检测摄像头…")
        self.status.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(bar)
        layout.addWidget(self.video, 1)
        layout.addWidget(self.status)
        escape = QAction(self)
        escape.setShortcut("Esc")
        escape.triggered.connect(self.close)
        self.addAction(escape)
        self.anchor_screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.watched_screens = set()
        self.watch_screens()
        QApplication.instance().screenAdded.connect(self.screens_changed)
        QApplication.instance().screenRemoved.connect(self.screens_changed)
        self.refresh_devices()
        QTimer.singleShot(0, self.pin_to_corner)

    def frame_received(self, frame):
        if frame.isValid():
            self.frames += 1
            if self.frames == 1:
                self.status.setText("实时预览 · 右键设置 · Esc 退出")
                print(f"PREVIEW_READY {frame.width()}x{frame.height()}", flush=True)

    def watch_screens(self):
        for screen in QGuiApplication.screens():
            if screen not in self.watched_screens:
                screen.availableGeometryChanged.connect(self.pin_to_corner)
                self.watched_screens.add(screen)

    def screens_changed(self, *_):
        screens = QGuiApplication.screens()
        self.watched_screens.intersection_update(screens)
        if self.anchor_screen not in screens:
            self.anchor_screen = QGuiApplication.primaryScreen()
        self.watch_screens()
        self.pin_to_corner()

    def pin_to_corner(self, *_):
        if self.anchor_screen is None:
            return
        area = self.anchor_screen.availableGeometry()
        margin = 12
        width = min(self.target_width, max(1, area.width() - margin * 2))
        height = min(round(width * 9 / 16) + 76, max(1, area.height() - margin * 2))
        self.resize(width, height)
        if self.manually_positioned:
            self.move_within_screen(self.pos())
        else:
            self.move(area.right() - width - margin + 1,
                      area.top() + (area.height() - height) // 2)

    def move_within_screen(self, position):
        area = self.anchor_screen.availableGeometry()
        x = max(area.left(), min(position.x(), area.right() - self.width() + 1))
        y = max(area.top(), min(position.y(), area.bottom() - self.height() + 1))
        self.move(QPoint(x, y))

    def refresh_devices(self):
        devices = QMediaDevices.videoInputs()
        previous = self.selected_id
        self.selector.blockSignals(True)
        self.selector.clear()
        for device in devices:
            self.selector.addItem(device.description(), device)
        chosen = next((i for i, d in enumerate(devices) if d.id() == previous), -1)
        if chosen < 0:
            chosen = next((i for i, d in enumerate(devices) if any(s in d.description().lower() for s in ("usb", "uvc", "external"))), 0 if devices else -1)
        self.selector.setCurrentIndex(chosen)
        self.selector.blockSignals(False)
        self.select_camera(chosen)

    def stop_camera(self):
        if self.camera is not None:
            self.camera.stop()
            self.session.setCamera(None)
            self.camera.deleteLater()
            self.camera = None

    def select_camera(self, index):
        self.stop_camera()
        self.frames = 0
        if index < 0:
            self.selected_id = None
            self.status.setText("未检测到摄像头，请连接 USB 摄像头。")
            return
        device = self.selector.itemData(index)
        self.selected_id = device.id()
        self.camera = QCamera(device, self)
        formats = [f for f in device.videoFormats() if f.resolution().width() <= 1280 and f.maxFrameRate() >= 24]
        if formats:
            self.camera.setCameraFormat(min(formats, key=lambda f: abs(f.resolution().width() - 1280) + abs(f.resolution().height() - 720)))
        self.camera.errorOccurred.connect(self.camera_error)
        self.session.setCamera(self.camera)
        self.status.setText("正在打开摄像头…")
        self.camera.start()

    def camera_error(self, error, message):
        self.status.setText("无法打开摄像头：" + message + "。请检查权限或摄像头占用情况。")
        print("CAMERA_ERROR " + message, file=sys.stderr, flush=True)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        for label, width in (("小窗口（320）", 320), ("中窗口（384）", 384), ("大窗口（640）", 640)):
            menu.addAction(label).triggered.connect(lambda checked=False, w=width: self.set_width(w))
        screens = menu.addMenu("显示屏幕")
        for screen in QGuiApplication.screens():
            screens.addAction(screen.name()).triggered.connect(lambda checked=False, s=screen: self.set_screen(s))
        menu.addAction("重新连接摄像头", self.refresh_devices)
        menu.addAction("恢复右侧居中", lambda: self.set_screen(self.anchor_screen))
        menu.addAction("退出", self.close)
        menu.exec(event.globalPos())

    def set_width(self, width):
        self.target_width = width
        self.pin_to_corner()

    def set_screen(self, screen):
        self.anchor_screen = screen
        self.manually_positioned = False
        self.pin_to_corner()

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("USB 摄像头预览")
    app.setDesktopFileName("usb-camera-preview")
    window = Preview()
    window.show()
    sys.exit(app.exec())
