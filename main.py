import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from tray_app import PauseTimerTrayApp


def _configure_macos_agent_app() -> None:
    if sys.platform != "darwin":
        return

    try:
        from AppKit import (
            NSApplication,
            NSApplicationActivationPolicyAccessory,
        )
    except ImportError:
        return

    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )


def main() -> int:
    app = QApplication(sys.argv)
    _configure_macos_agent_app()
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
