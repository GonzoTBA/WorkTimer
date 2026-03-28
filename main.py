import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from tray_app import PauseTimerTrayApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Pause Timer")
    app.setOrganizationName("WorkTimer")
    app.setQuitOnLastWindowClosed(False)

    if not PauseTimerTrayApp.is_tray_available():
        QMessageBox.critical(
            None,
            "Tray no disponible",
            "Este sistema no soporta iconos en la barra superior. La app se cerrara.",
        )
        return 1

    tray_app = PauseTimerTrayApp(app)
    tray_app.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
