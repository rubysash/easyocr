"""
ocr_subprocess.py - Standalone OCR runner, spawned as a child process.
Uses EasyOCR (cross-platform, no Windows-only APIs required).
Wraps ALL code including imports in try/except so any failure
reaches stdout as JSON rather than dying silently.
"""

import sys
import json


def main():
    try:
        from pathlib import Path

        if len(sys.argv) < 2:
            _out(False, error="No image path supplied")
            return

        image_path = sys.argv[1]

        if not Path(image_path).exists():
            _out(False, error=f"Image file not found: {image_path}")
            return

        try:
            import easyocr
        except Exception:
            import traceback
            _out(False, error=f"easyocr import failed:\n{traceback.format_exc()}\n\nRun: pip install easyocr")
            return

        try:
            import warnings
            warnings.filterwarnings("ignore", message=".*pin_memory.*")

            # gpu=False keeps it CPU-only and avoids CUDA/DLL conflicts.
            # verbose=False suppresses model-download progress spam on stdout.
            reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            results = reader.readtext(image_path, detail=0, paragraph=True)
            lines = [str(r) for r in results]
        except Exception:
            import traceback
            _out(False, error=f"EasyOCR recognition failed:\n{traceback.format_exc()}")
            return

        _out(True, lines=lines)

    except Exception:
        import traceback
        _out(False, error=f"Unhandled top-level exception:\n{traceback.format_exc()}")


def _out(ok, error=None, lines=None):
    payload = {"ok": ok}
    if error:
        payload["error"] = error
    if lines is not None:
        payload["lines"] = lines
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()