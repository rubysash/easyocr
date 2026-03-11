"""
main.py - Entry point
Run: python main.py
Log output: ocr_debug.log (same folder as script)
"""

import sys
import logging
import traceback
from pathlib import Path

# ── Logging setup (file + stdout) ─────────────────────────────────────────────
log_path = Path(__file__).parent / "ocr_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("main")
log.info("=== OCR Tool starting ===")
log.info(f"Python: {sys.version}")
log.info(f"Platform: {sys.platform}")

# ── Qt import ─────────────────────────────────────────────────────────────────
log.info("Importing PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication
    log.info("PyQt5 imported OK")
except Exception:
    log.critical("PyQt5 import FAILED:\n" + traceback.format_exc())
    sys.exit(1)

# ── winsdk import check ───────────────────────────────────────────────────────
log.info("Checking winsdk availability...")
try:
    import winsdk
    log.info("winsdk imported OK")
except Exception:
    log.warning("winsdk import FAILED (will surface in UI when OCR runs):\n" + traceback.format_exc())

# ── App window ────────────────────────────────────────────────────────────────
def main():
    log.info("Creating QApplication...")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    log.info("QApplication created OK")

    log.info("Importing MainWindow from gui...")
    try:
        from gui import MainWindow
        log.info("MainWindow imported OK")
    except Exception:
        log.critical("gui.py import FAILED:\n" + traceback.format_exc())
        sys.exit(1)

    log.info("Instantiating MainWindow...")
    try:
        win = MainWindow()
        log.info("MainWindow instantiated OK")
    except Exception:
        log.critical("MainWindow() FAILED:\n" + traceback.format_exc())
        sys.exit(1)

    log.info("Calling win.show()...")
    win.show()
    log.info("Window shown — entering event loop")

    code = app.exec_()
    log.info(f"Event loop exited with code {code}")
    # Do not call sys.exit() — let the process end naturally so logs flush


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.critical("Unhandled exception in main():\n" + traceback.format_exc())
        sys.exit(1)