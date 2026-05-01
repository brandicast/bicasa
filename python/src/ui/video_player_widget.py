import os
import sys
import subprocess
import shutil
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QUrl, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage

import logging
logger = logging.getLogger(__name__)

# Read the platform flag set by bicasa.py at startup
VIDEO_SUPPORT = os.environ.get("BICASA_VIDEO_SUPPORT", "1") == "1"


class VideoPlayerWidget(QWidget):
    """
    Cross-platform video player widget.

    - Native Linux / Windows : uses QMediaPlayer + QVideoSink (hardware-accelerated)
    - WSL2                   : shows an informative message; offers to open with external player
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_path = None
        self._process = None

        self._layout = QVBoxLayout(self)

        if VIDEO_SUPPORT:
            self._init_player()
        else:
            self._init_unsupported_ui()

    # ------------------------------------------------------------------
    # Branch A: Native Linux / Windows — full QMediaPlayer support
    # ------------------------------------------------------------------
    def _init_player(self):
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink

        self._is_processing_frame = False

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.addWidget(self.video_label, stretch=1)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.video_sink = QVideoSink()
        self.media_player.setVideoSink(self.video_sink)
        self.video_sink.videoFrameChanged.connect(self._on_frame_changed)

        # Controls
        controls = QHBoxLayout()

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self._toggle_play)
        controls.addWidget(self.play_btn)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self._set_position)
        controls.addWidget(self.slider)

        self.time_label = QLabel("00:00 / 00:00")
        controls.addWidget(self.time_label)

        self.mute_btn = QPushButton("🔇 Mute")
        self.mute_btn.clicked.connect(self._toggle_mute)
        controls.addWidget(self.mute_btn)

        self._layout.addLayout(controls)

        self.media_player.positionChanged.connect(self._position_changed)
        self.media_player.durationChanged.connect(self._duration_changed)
        self.media_player.errorOccurred.connect(self._on_error)

        # Signal to marshal frame from decoder thread → GUI thread
        self._frame_signal = _FrameSignalBridge()
        self._frame_signal.frame_ready.connect(self._update_video_label)

    def _on_frame_changed(self, frame):
        if self._is_processing_frame:
            return
        if frame.isValid():
            self._is_processing_frame = True
            image = frame.toImage().copy()  # deep copy — safe across threads
            if not image.isNull():
                self._frame_signal.frame_ready.emit(image)
            else:
                self._is_processing_frame = False

    def _update_video_label(self, image):
        try:
            w = self.video_label.size().width()
            h = self.video_label.size().height()
            if w <= 0 or h <= 0:
                return
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
            self.video_label.setPixmap(scaled)
        finally:
            self._is_processing_frame = False

    def _toggle_play(self):
        from PySide6.QtMultimedia import QMediaPlayer as MP
        if self.media_player.playbackState() == MP.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶ Play")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸ Pause")

    def _toggle_mute(self):
        muted = self.audio_output.isMuted()
        self.audio_output.setMuted(not muted)
        self.mute_btn.setText("🔊 Unmute" if not muted else "🔇 Mute")

    def _position_changed(self, position):
        self.slider.blockSignals(True)
        self.slider.setValue(position)
        self.slider.blockSignals(False)
        self._update_time_label()

    def _duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self._update_time_label()

    def _set_position(self, position):
        self.media_player.setPosition(position)

    def _update_time_label(self):
        pos = self.media_player.position() // 1000
        dur = self.media_player.duration() // 1000
        self.time_label.setText(f"{pos//60:02d}:{pos%60:02d} / {dur//60:02d}:{dur%60:02d}")

    def _on_error(self, error, msg):
        logger.error(f"QMediaPlayer error {error}: {msg}")

    # ------------------------------------------------------------------
    # Branch B: WSL2 — no hardware support, show fallback UI
    # ------------------------------------------------------------------
    def _init_unsupported_ui(self):
        bg = QLabel()
        bg.setStyleSheet("background-color: #1a1a1a;")
        bg.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(bg, stretch=1)

        msg = QLabel(
            "⚠️  影片播放在 WSL2 環境下不支援\n\n"
            "原因：WSL2 缺少音訊伺服器（PulseAudio）且 OpenGL 被停用\n\n"
            "請在原生 Linux 或 Windows 環境下使用完整功能，\n"
            "或點擊下方按鈕以外部播放器開啟。"
        )
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("color: #cccccc; font-size: 14px;")
        self._layout.addWidget(msg)

        btn = QPushButton("🎬  以外部播放器開啟（mpv / vlc）")
        btn.clicked.connect(self._open_external)
        btn.setFixedHeight(40)
        self._layout.addWidget(btn)

    def _open_external(self):
        if not self._file_path:
            return
        player = shutil.which("mpv") or shutil.which("vlc") or shutil.which("ffplay")
        if player:
            logger.info(f"Opening video with external player: {player}")
            self._process = subprocess.Popen([player, self._file_path])
        else:
            logger.warning("No external video player found. Install mpv: sudo apt install mpv")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "找不到外部播放器",
                "找不到 mpv / vlc / ffplay。\n請執行：\n  sudo apt install mpv"
            )

    # ------------------------------------------------------------------
    # Common interface
    # ------------------------------------------------------------------
    def load_video(self, file_path):
        self._file_path = file_path
        if VIDEO_SUPPORT:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.play_btn.setText("▶ Play")

    def stop(self):
        logger.debug("VideoPlayerWidget.stop()")
        if VIDEO_SUPPORT and hasattr(self, 'media_player'):
            self.media_player.stop()
            if hasattr(self, 'video_label'):
                self.video_label.clear()
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process = None


class _FrameSignalBridge(QWidget):
    """
    Lightweight QObject used only to carry a Signal.
    Keeps the frame pipeline decoupled from VideoPlayerWidget itself.
    """
    frame_ready = Signal(QImage)
