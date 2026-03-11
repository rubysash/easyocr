"""
ocr_backend.py - Spawns ocr_subprocess.py and reads JSON result.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path

log = logging.getLogger("ocr_backend")

_SUBPROCESS_SCRIPT = Path(__file__).parent / "ocr_subprocess.py"

_WIN32_CODES = {
    0xC0000005: "ACCESS_VIOLATION (0xC0000005) — native DLL crash at startup",
    0xC000007B: "INVALID_IMAGE_FORMAT (0xC000007B) — DLL arch mismatch (32 vs 64-bit)",
    0xC0000034: "OBJECT_NAME_NOT_FOUND (0xC0000034)",
    3221225477: "ACCESS_VIOLATION (0xC0000005) — native DLL crash at startup",
}

# PATH fragments from packages whose native DLLs can crash subprocess startup.
_PATH_BLOCKLIST = ("cuda", "nvidia", "cudnn", "cufft", "cublas")


def _make_startupinfo():
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return si
    return None


def _clean_env() -> dict:
    """Sanitize the child environment to avoid rogue DLL crashes."""
    env = os.environ.copy()

    # --- Sanitize PATH (Windows only) ---
    if sys.platform == "win32":
        original_path = env.get("PATH", "")
        entries = original_path.split(os.pathsep)
        clean_path = [e for e in entries
                      if not any(kw in e.lower() for kw in _PATH_BLOCKLIST)]
        removed = [e for e in entries if e not in clean_path]
        if removed:
            log.debug(f"_clean_env: removed {len(removed)} PATH entries:\n  " + "\n  ".join(removed))
        env["PATH"] = os.pathsep.join(clean_path)

    # --- Sanitize PYTHONPATH ---
    original_pypath = env.get("PYTHONPATH", "")
    if original_pypath:
        py_entries = original_pypath.split(os.pathsep)
        clean_py = [e for e in py_entries
                    if not any(kw in e.lower() for kw in _PATH_BLOCKLIST)]
        removed_py = [e for e in py_entries if e not in clean_py]
        if removed_py:
            log.debug(f"_clean_env: removed {len(removed_py)} PYTHONPATH entries:\n  " + "\n  ".join(removed_py))
        env["PYTHONPATH"] = os.pathsep.join(clean_py)

    env["PYTHONNOUSERSITE"] = "1"
    return env


def _preflight_check(env: dict) -> str | None:
    """Verify Python can start cleanly in the sanitized environment."""
    log.debug("Running pre-flight Python check...")
    try:
        r = subprocess.run(
            [sys.executable, "-c", "print('preflight_ok')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=_make_startupinfo(),
            env=env,
            timeout=15,
        )
        out = r.stdout.decode("utf-8", errors="replace").strip()
        err = r.stderr.decode("utf-8", errors="replace").strip()
        log.debug(f"Pre-flight rc={r.returncode} out={out!r} err={err!r}")
        if out == "preflight_ok":
            return None
        rc = r.returncode
        rc_label = (_WIN32_CODES.get(rc) or _WIN32_CODES.get(rc & 0xFFFFFFFF)
                    or f"0x{rc & 0xFFFFFFFF:08X}")
        return (
            f"Python itself crashed in the subprocess environment.\n"
            f"Return code: {rc_label}\n"
            f"stderr: {err or '(empty)'}\n\n"
            "Try creating a fresh venv with only: pip install easyocr pyqt5"
        )
    except Exception as exc:
        return f"Pre-flight check itself failed: {exc}"


def run_ocr(image_path: str) -> str:
    log.info(f"Spawning OCR subprocess for: {image_path}")

    if not _SUBPROCESS_SCRIPT.exists():
        raise FileNotFoundError(f"ocr_subprocess.py not found at {_SUBPROCESS_SCRIPT}")

    env = _clean_env()

    preflight_err = _preflight_check(env)
    if preflight_err:
        raise RuntimeError(preflight_err)
    log.debug("Pre-flight passed — spawning OCR subprocess")

    proc = subprocess.run(
        [sys.executable, str(_SUBPROCESS_SCRIPT), image_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=_make_startupinfo(),
        env=env,
        timeout=120,   # EasyOCR model load can take 30-60 s on first run
    )

    stdout = proc.stdout.decode("utf-8", errors="replace").strip()
    stderr = proc.stderr.decode("utf-8", errors="replace").strip()

    log.debug(f"Return code : {proc.returncode}")
    log.debug(f"stdout      : {stdout[:500] if stdout else '(empty)'}")
    if stderr:
        log.warning(f"stderr      :\n{stderr}")

    if not stdout:
        rc = proc.returncode
        rc_label = (
            _WIN32_CODES.get(rc)
            or _WIN32_CODES.get(rc & 0xFFFFFFFF)
            or f"0x{rc & 0xFFFFFFFF:08X}"
        )
        raise RuntimeError(
            f"OCR subprocess produced no output.\n"
            f"Return code : {rc_label}\n\n"
            f"stderr:\n{stderr or '(empty)'}\n\n"
            "Run manually to see the full error:\n"
            f"  python ocr_subprocess.py \"{image_path}\""
        )

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Could not parse subprocess output:\n{stdout}")

    if not data.get("ok"):
        raise RuntimeError(data.get("error", "Unknown OCR error"))

    lines = data["lines"]
    log.info(f"OCR subprocess returned {len(lines)} lines")
    return "\n".join(lines)