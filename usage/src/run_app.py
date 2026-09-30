"""Production entrypoint; validation status is tracked in IMPLEMENTATION."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import TracebackType

from PySide6.QtCore import QLibraryInfo, QLocale, QTimer, QTranslator
from PySide6.QtWidgets import QApplication, QMessageBox

from usage_app.credentials import CredentialError
from usage_app.desktop import DesktopLeaf, SingleInstance, tray_icon
from usage_app.diagnostics import DiagnosticLog
from usage_app.runtime import UsageRuntime
from usage_app.startup_ui import startup_error
from usage_app.storage import StorageError, default_data_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="usage")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--expanded", action="store_true")
    parser.add_argument("--settings", action="store_true", help="Open the settings window on startup")
    parser.add_argument("--reduced-motion", action="store_true")
    parser.add_argument("--detail", choices=("codex", "glm", "deepseek"), default="")
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("usage")
    app.setWindowIcon(tray_icon())
    app.setStyleSheet("QToolTip { color: #1e2119; background: #f5f2e9; border: 1px solid #9ca184; padding: 4px 6px; font: 10pt 'Microsoft YaHei UI'; }")
    translator = QTranslator(app)
    if translator.load(QLocale.system(), "qtbase", "_", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
    data_dir = args.data_dir
    runtime: UsageRuntime | None = None
    diagnostics: DiagnosticLog | None = None
    try:
        data_dir = data_dir or default_data_dir()
        instance = SingleInstance(data_dir)
        if not instance.acquire():
            return 0
        diagnostics = DiagnosticLog(data_dir)
        diagnostics.write("start")
        runtime = UsageRuntime(data_dir)
        widget = DesktopLeaf(runtime, reduced_motion=args.reduced_motion)
    except (StorageError, CredentialError) as error:
        if runtime is not None:
            runtime.stop()
        if diagnostics is not None:
            diagnostics.write("storage_failed", error=error)
        startup_error(error, data_dir).exec()
        return 1
    instance.on_restore(widget.restore_from_tray)
    fault_notice: list[QMessageBox] = []
    def unexpected(kind: type[BaseException], error: BaseException, traceback: TracebackType | None) -> None:
        if diagnostics is not None:
            diagnostics.write("unexpected_error", error=error, traceback=traceback)
        if not fault_notice:
            message = startup_error(RuntimeError(), data_dir)
            message.setWindowTitle("usage · 运行遇到问题")
            message.setText("程序运行遇到问题，请重新启动usage。")
            message.finished.connect(lambda result: widget.quit_app())
            fault_notice.append(message)  # One notice per session, no repeated popups.
            message.show()
    sys.excepthook = unexpected
    if args.expanded or args.detail:
        widget.set_expansion_progress(1)
    widget.set_detail(args.detail)
    widget.show()
    app.aboutToQuit.connect(runtime.stop)
    app.aboutToQuit.connect(widget.snippets.stop)
    app.aboutToQuit.connect(widget.reminders.stop)
    app.aboutToQuit.connect(lambda: diagnostics.write("quit") if diagnostics is not None else None)
    if args.settings:
        QTimer.singleShot(0, widget.open_text_settings)
    if args.capture:
        widget._pulse.stop()
        def capture() -> None:
            args.capture.parent.mkdir(parents=True, exist_ok=True)
            widget.grab().save(str(args.capture))
            app.quit()
        QTimer.singleShot(11_000, capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
