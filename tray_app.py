from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QCursor, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
)

from settings_manager import SettingsManager
from timer_model import TimerModel, TimerState


PRESET_MINUTES = [5, 15, 25, 60]


def format_seconds(total_seconds: int) -> str:
    minutes, seconds = divmod(max(0, total_seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"


class TimerWindow(QFrame):
    def __init__(self, settings: SettingsManager, model: TimerModel) -> None:
        super().__init__()
        self.settings = settings
        self.model = model
        self._preset_buttons: list[QPushButton] = []

        self.setWindowTitle("Pause Timer")
        self.setWindowFlags(
            Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setObjectName("timerWindow")
        self.setFixedWidth(340)

        self._build_ui()
        self._apply_style()
        self.refresh_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Pause Timer")
        title.setObjectName("titleLabel")
        root.addWidget(title)

        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.time_label)

        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(8)
        for minutes in PRESET_MINUTES:
            button = QPushButton(f"{minutes} min")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, value=minutes: self.set_duration_minutes(value)
            )
            self._preset_buttons.append(button)
            presets_layout.addWidget(button)
        root.addLayout(presets_layout)

        duration_layout = QGridLayout()
        duration_layout.setHorizontalSpacing(10)
        duration_layout.setVerticalSpacing(8)

        duration_label = QLabel("Minutos")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 240)
        self.duration_input.setSuffix(" min")
        self.duration_input.setValue(self.settings.load_duration_minutes())
        self.duration_input.valueChanged.connect(self._on_duration_changed)

        message_label = QLabel("Mensaje final")
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Haz una pausa")
        self.message_input.setText(self.settings.load_message())
        self.message_input.editingFinished.connect(self._persist_message)

        duration_layout.addWidget(duration_label, 0, 0)
        duration_layout.addWidget(self.duration_input, 0, 1)
        duration_layout.addWidget(message_label, 1, 0)
        duration_layout.addWidget(self.message_input, 1, 1)
        root.addLayout(duration_layout)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Resume")
        self.reset_button = QPushButton("Reset")

        self.start_button.clicked.connect(self.start_timer)
        self.pause_button.clicked.connect(self.pause_timer)
        self.resume_button.clicked.connect(self.resume_timer)
        self.reset_button.clicked.connect(self.reset_timer)

        controls.addWidget(self.start_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.resume_button)
        controls.addWidget(self.reset_button)
        root.addLayout(controls)

        hint = QLabel("Utilidad compacta para pausas rapidas")
        hint.setObjectName("hintLabel")
        root.addWidget(hint)

        footer = QHBoxLayout()
        footer.addStretch()

        self.quit_button = QPushButton("Quit")
        self.quit_button.setObjectName("quitButton")
        self.quit_button.clicked.connect(self._quit_application)
        footer.addWidget(self.quit_button)

        root.addLayout(footer)

        self.set_duration_minutes(self.duration_input.value(), persist=False)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QFrame#timerWindow {
                background: #17191d;
                border: 1px solid #2a2f39;
                border-radius: 18px;
            }
            QLabel {
                color: #e9edf4;
            }
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: 700;
            }
            QLabel#timeLabel {
                font-size: 42px;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 8px 0;
            }
            QLabel#hintLabel {
                color: #8f98a8;
                font-size: 12px;
            }
            QPushButton {
                background: #232833;
                color: #eef2f8;
                border: 1px solid #313847;
                border-radius: 10px;
                padding: 8px 10px;
                min-height: 16px;
            }
            QPushButton:hover {
                background: #2b3140;
            }
            QPushButton:pressed {
                background: #1f2430;
            }
            QPushButton:checked {
                background: #4f7cff;
                border-color: #4f7cff;
            }
            QPushButton#quitButton {
                padding: 6px 12px;
                min-height: 14px;
            }
            QLineEdit, QSpinBox {
                background: #111318;
                color: #eef2f8;
                border: 1px solid #2d3442;
                border-radius: 10px;
                padding: 8px 10px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                border: none;
            }
            """
        )

    def _persist_message(self) -> None:
        self.settings.save_message(self.message_input.text())

    def _on_duration_changed(self, minutes: int) -> None:
        self.settings.save_duration_minutes(minutes)
        if self.model.state in {TimerState.IDLE, TimerState.FINISHED}:
            self.model.set_initial_duration(minutes * 60)
        self._sync_presets(minutes)
        self.refresh_ui()

    def _sync_presets(self, minutes: int) -> None:
        for button, preset in zip(self._preset_buttons, PRESET_MINUTES):
            button.setChecked(preset == minutes)

    def set_duration_minutes(self, minutes: int, persist: bool = True) -> None:
        self.duration_input.blockSignals(True)
        self.duration_input.setValue(minutes)
        self.duration_input.blockSignals(False)
        self._sync_presets(minutes)
        if persist:
            self._on_duration_changed(minutes)

    def selected_minutes(self) -> int:
        return self.duration_input.value()

    def final_message(self) -> str:
        message = self.message_input.text().strip() or "Haz una pausa"
        return message

    def start_timer(self) -> None:
        minutes = self.selected_minutes()
        self.settings.save_duration_minutes(minutes)
        self.settings.save_message(self.final_message())
        self.model.start(minutes * 60)
        self.refresh_ui()

    def pause_timer(self) -> None:
        self.model.pause()
        self.refresh_ui()

    def resume_timer(self) -> None:
        self.settings.save_message(self.final_message())
        self.model.resume()
        self.refresh_ui()

    def reset_timer(self) -> None:
        self.model.reset()
        self.refresh_ui()

    def _quit_application(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def refresh_ui(self) -> None:
        snapshot = self.model.snapshot()
        self.time_label.setText(format_seconds(snapshot.remaining_seconds))

        can_edit_duration = snapshot.state in {TimerState.IDLE, TimerState.FINISHED}
        self.duration_input.setEnabled(can_edit_duration)
        for button in self._preset_buttons:
            button.setEnabled(can_edit_duration)

        self.start_button.setEnabled(snapshot.state in {TimerState.IDLE, TimerState.FINISHED})
        self.pause_button.setEnabled(snapshot.state == TimerState.RUNNING)
        self.resume_button.setEnabled(snapshot.state == TimerState.PAUSED)
        self.reset_button.setEnabled(snapshot.state != TimerState.IDLE)


class PauseTimerTrayApp:
    def __init__(self, app) -> None:
        self.app = app
        self.settings = SettingsManager()
        self.model = TimerModel(self.settings.load_duration_minutes() * 60)
        self.window = TimerWindow(self.settings, self.model)
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(250)
        self.refresh_timer.timeout.connect(self._on_refresh_tick)

        self.tray_icon = QSystemTrayIcon(self._load_icon(), self.app)
        self.tray_icon.setToolTip("Pause Timer")
        self.tray_icon.activated.connect(self._on_tray_activated)

    @staticmethod
    def is_tray_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def _load_icon(self) -> QIcon:
        icon_path = Path(__file__).parent / "resources" / "tray_icon.svg"
        if icon_path.exists():
            return QIcon(str(icon_path))
        return self.window.style().standardIcon(self.window.style().SP_ComputerIcon)

    def show(self) -> None:
        self.tray_icon.show()
        self.refresh_timer.start()

    def open_window(self) -> None:
        self.window.refresh_ui()
        self._position_window()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def toggle_window(self) -> None:
        if self.window.isVisible():
            self.window.hide()
            return
        self.open_window()

    def _position_window(self) -> None:
        tray_geometry = self.tray_icon.geometry()
        anchor_pos = (
            tray_geometry.center() if tray_geometry.isValid() else QCursor.pos()
        )
        screen = QGuiApplication.screenAt(anchor_pos) or QGuiApplication.screenAt(
            QCursor.pos()
        )

        if screen is None:
            x = max(16, anchor_pos.x() - self.window.width() // 2)
            y = max(16, anchor_pos.y() + 18)
            self.window.move(QPoint(x, y))
            return

        available = screen.availableGeometry()
        x = anchor_pos.x() - self.window.width() // 2
        y = anchor_pos.y() + 18

        x = max(available.left() + 16, x)
        x = min(x, available.right() - self.window.width() - 16)
        y = max(available.top() + 16, y)
        y = min(y, available.bottom() - self.window.height() - 16)
        self.window.move(QPoint(x, y))

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        }:
            self.toggle_window()

    def _on_refresh_tick(self) -> None:
        finished_now = self.model.tick()
        self.window.refresh_ui()

        if finished_now:
            message = self.window.final_message()
            self.settings.save_message(message)
            self.tray_icon.showMessage(
                "Pause Timer",
                message,
                self.tray_icon.icon(),
                5000,
            )
