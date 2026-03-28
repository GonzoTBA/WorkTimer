from __future__ import annotations

from PySide6.QtCore import QSettings


class SettingsManager:
    def __init__(self) -> None:
        self._settings = QSettings("WorkTimer", "PauseTimer")

    def load_duration_minutes(self, default: int = 15) -> int:
        value = self._settings.value("timer/last_duration_minutes", default, type=int)
        return max(1, value)

    def save_duration_minutes(self, minutes: int) -> None:
        self._settings.setValue("timer/last_duration_minutes", max(1, minutes))
        self._settings.sync()

    def load_message(self, default: str = "Haz una pausa") -> str:
        value = self._settings.value("timer/final_message", default, type=str)
        return (value or default).strip() or default

    def save_message(self, message: str) -> None:
        cleaned = (message or "").strip() or "Haz una pausa"
        self._settings.setValue("timer/final_message", cleaned)
        self._settings.sync()
