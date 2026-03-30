"""
gui.py - MainWindow
"""

import logging
import tempfile
import traceback
from pathlib import Path

log = logging.getLogger("gui")

log.debug("gui.py module loading...")

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QProgressBar,
    QSplitter, QStatusBar, QFrame, QScrollArea, QSizePolicy,
    QApplication,
)
from PyQt6.QtGui import QPixmap, QFont, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QSize

log.debug("PyQt6 widgets imported OK")

from worker import OCRWorker
log.debug("OCRWorker imported OK")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        log.debug("MainWindow.__init__ start")
        self.image_path: str | None = None
        self.worker: OCRWorker | None = None

        self.setWindowTitle("OCR Tool")
        self.setMinimumSize(1050, 680)

        self._build_ui()
        self.status_bar.showMessage("Ready — open an image to begin.")
        log.debug("MainWindow.__init__ complete")

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        log.debug("_build_ui start")
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        root.addLayout(self._build_toolbar())
        root.addWidget(self._build_progress())
        root.addWidget(self._build_splitter(), stretch=1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Ctrl+V shortcut for pasting clipboard images
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        paste_shortcut.activated.connect(self.paste_image)

        log.debug("_build_ui complete")

    def _build_toolbar(self):
        log.debug("Building toolbar")
        toolbar = QHBoxLayout()

        self.btn_open = QPushButton("Open Image...")
        self.btn_open.setFixedHeight(34)
        self.btn_open.clicked.connect(self.open_image)

        self.btn_paste = QPushButton("Paste Image (Ctrl+V)")
        self.btn_paste.setFixedHeight(34)
        self.btn_paste.clicked.connect(self.paste_image)

        self.btn_run = QPushButton("Run OCR")
        self.btn_run.setFixedHeight(34)
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_ocr)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFixedHeight(34)
        self.btn_clear.clicked.connect(self.clear_all)

        self.btn_copy = QPushButton("Copy All")
        self.btn_copy.setFixedHeight(34)
        self.btn_copy.clicked.connect(self.copy_all)

        engine_badge = QLabel("Engine: EasyOCR  |  First run downloads model (~100 MB)")
        engine_badge.setStyleSheet("font-size: 9pt; opacity: 0.7;")

        toolbar.addWidget(self.btn_open)
        toolbar.addWidget(self.btn_paste)
        toolbar.addWidget(self.btn_run)
        toolbar.addWidget(self.btn_clear)
        toolbar.addSpacing(16)
        toolbar.addWidget(self.btn_copy)
        toolbar.addStretch()
        toolbar.addWidget(engine_badge)
        return toolbar

    def _build_progress(self):
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(5)
        self.progress.setVisible(False)
        return self.progress

    def _build_splitter(self):
        log.debug("Building splitter panels")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_preview_panel())
        splitter.addWidget(self._build_output_panel())
        splitter.setSizes([440, 610])
        return splitter

    def _build_preview_panel(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("Image Preview"))

        self.img_label = QLabel("No image loaded")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("")
        self.img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.img_label)
        layout.addWidget(scroll)
        return frame

    def _build_output_panel(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        header.addWidget(QLabel("OCR Output"))
        header.addStretch()
        self.char_count = QLabel("")
        self.char_count.setStyleSheet("font-size: 9pt;")
        header.addWidget(self.char_count)
        layout.addLayout(header)

        self.text_out = QTextEdit()
        self.text_out.setFont(QFont("Courier New", 10))
        self.text_out.setAcceptRichText(False)
        self.text_out.setPlaceholderText(
            "OCR output will appear here.\n\n"
            "Ctrl+A  — select all (newlines preserved)\n"
            "Ctrl+C  — copy\n"
            "Or use the Copy All button above."
        )
        self.text_out.textChanged.connect(self._update_char_count)
        layout.addWidget(self.text_out)
        return frame

    # ── Actions ───────────────────────────────────────────────────────────────

    def _load_image(self, path: str, title: str):
        """Set image_path, show preview, and enable Run OCR."""
        self.image_path = path
        self.setWindowTitle(f"OCR Tool — {title}")

        pix = QPixmap(path)
        if not pix.isNull():
            scaled = pix.scaled(QSize(440, 580), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(scaled)
            log.debug("Preview loaded OK")
        else:
            self.img_label.setText("Preview unavailable")
            log.warning("QPixmap returned null for selected file")

        self.btn_run.setEnabled(True)
        self.status_bar.showMessage(f"Loaded: {title}")

    def open_image(self):
        log.debug("open_image called")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif)"
        )
        if not path:
            log.debug("No file selected")
            return

        log.info(f"Image selected: {path}")
        self._load_image(path, Path(path).name)

    def paste_image(self):
        log.debug("paste_image called")
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        # Try to get an image from the clipboard
        if mime.hasImage():
            pix = QPixmap(clipboard.image())
        elif mime.hasUrls():
            # Handle file paths copied/dragged (e.g. right-click → Copy in Explorer)
            urls = mime.urls()
            local = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if local:
                log.info(f"Clipboard contains file URL: {local[0]}")
                self._load_image(local[0], Path(local[0]).name)
                return
            log.debug("Clipboard URLs are not local files")
            self.status_bar.showMessage("Clipboard does not contain a usable image.")
            return
        else:
            log.debug("Clipboard has no image data")
            self.status_bar.showMessage("Clipboard does not contain an image. Copy or screenshot one first.")
            return

        if pix.isNull():
            log.warning("Clipboard image converted to null QPixmap")
            self.status_bar.showMessage("Clipboard image could not be read.")
            return

        # Save to a temp file so the existing OCR pipeline can use it
        tmp = tempfile.NamedTemporaryFile(
            suffix=".png", prefix="ocr_paste_", delete=False
        )
        tmp.close()
        pix.save(tmp.name, "PNG")
        log.info(f"Clipboard image saved to temp file: {tmp.name}")

        self._load_image(tmp.name, "Pasted image")

    def run_ocr(self):
        log.info(f"run_ocr called — image: {self.image_path}")
        if not self.image_path:
            return

        self.text_out.clear()
        self._set_busy(True)
        self.status_bar.showMessage(
            "Running OCR… (first run may take 30–60 s while the model loads)"
        )

        log.debug("Creating OCRWorker...")
        self.worker = OCRWorker(self.image_path)
        self.worker.finished.connect(self._on_ocr_finished)
        self.worker.error.connect(self._on_ocr_error)
        self.worker.status.connect(self.status_bar.showMessage)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.start()
        log.debug("OCRWorker thread started")

    def clear_all(self):
        log.debug("clear_all called")
        self.text_out.clear()
        self.img_label.clear()
        self.img_label.setText("No image loaded")
        self.image_path = None
        self.btn_run.setEnabled(False)
        self.setWindowTitle("OCR Tool")
        self.status_bar.showMessage("Cleared.")

    def copy_all(self):
        log.debug("copy_all called")
        self.text_out.selectAll()
        self.text_out.copy()
        self.status_bar.showMessage("Copied to clipboard.")

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_ocr_finished(self, text: str):
        log.info(f"_on_ocr_finished slot entered — {len(text)} chars")
        self._set_busy(False)
        self.text_out.setPlainText(text)
        lines = text.count("\n") + 1 if text.strip() else 0
        self.status_bar.showMessage(
            f"Done — {lines} line(s) detected. Ctrl+A then Ctrl+C to copy."
        )
        log.info("_on_ocr_finished complete")

    def _on_ocr_error(self, msg: str):
        log.error(f"OCR error signal received:\n{msg}")
        self._set_busy(False)
        self.text_out.setPlainText(f"ERROR:\n\n{msg}")
        self.status_bar.showMessage("OCR failed — see output panel.")

    def _set_busy(self, busy: bool):
        log.debug(f"_set_busy({busy})")
        self.progress.setVisible(busy)
        self.btn_run.setEnabled(not busy)
        self.btn_open.setEnabled(not busy)
        self.btn_paste.setEnabled(not busy)

    def _update_char_count(self):
        t = self.text_out.toPlainText()
        self.char_count.setText(f"{len(t)} chars" if t else "")