"""
worker.py - OCRWorker QThread
"""

import logging
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

log = logging.getLogger("worker")


class OCRWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)
    status   = pyqtSignal(str)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
        log.debug(f"OCRWorker created for: {image_path}")

    def run(self):
        log.info("OCRWorker.run() started")
        try:
            log.debug("Importing ocr_backend...")
            from ocr_backend import run_ocr
            log.debug("ocr_backend imported OK")

            self.status.emit("Running OCR...")
            log.info("Calling run_ocr()...")
            text = run_ocr(self.image_path)
            log.info(f"run_ocr() returned {len(text)} chars, {text.count(chr(10))+1} lines")
            log.debug("Emitting finished signal...")
            self.finished.emit(text)
            log.debug("finished signal emitted OK")

        except ImportError as e:
            msg = f"Missing dependency: {e}\n\nRun:  pip install winsdk Pillow pyqt5"
            log.error(msg)
            self.error.emit(msg)

        except Exception:
            msg = traceback.format_exc()
            log.error(f"OCRWorker unhandled exception:\n{msg}")
            self.error.emit(msg)

        log.info("OCRWorker.run() exiting")