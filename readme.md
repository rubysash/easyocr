# Local OCR Tool

A fully **offline, local OCR tool** built with EasyOCR and PyQt6. Images are processed entirely on your machine — **nothing is uploaded to any cloud service.**

---

## How It Works

The app uses a layered subprocess architecture to prevent native DLL conflicts (common with PyTorch/CUDA on Windows) from crashing the UI:

```
main.py  (PyQt6 UI)
  └── OCRWorker  (QThread — worker.py)
        └── ocr_backend.py  (sanitizes env, spawns subprocess)
              └── ocr_subprocess.py  (isolated child process — runs EasyOCR)
```

1. **`worker.py`** — A `QThread` that keeps the UI responsive while OCR runs. Emits `finished`, `error`, and `status` signals.
2. **`ocr_backend.py`** — Sanitizes the environment (strips CUDA/NVIDIA/cuDNN entries from `PATH` and `PYTHONPATH` to prevent DLL crashes), runs a pre-flight Python check, then spawns `ocr_subprocess.py` as a child process. Parses the JSON result from stdout.
3. **`ocr_subprocess.py`** — A self-contained script that imports EasyOCR, runs recognition (`gpu=False`, CPU-only), and writes a JSON result to stdout. All errors are caught and returned as JSON so nothing fails silently.

---

## Requirements

- **Windows** (tested), Linux/macOS compatible
- **Python 3.9+**
- A virtual environment (**required**)

---

## Installation

> **Install order matters.** PyTorch and torchvision ship CPU-only wheels through their own download index — they are **not on PyPI**. You must install them first with the `--index-url` flag before running `pip install -r requirements.txt`, or pip will fail trying to find the `+cpu` tagged versions.

### 1. Create and activate a virtual environment

```bat
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

#### Option A — Automated (Windows)

```bat
install.bat
```

#### Option B — Manual

**Step 1: Install PyTorch + torchvision (CPU-only) from the PyTorch wheel index**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

This installs the CPU-only builds (`torch==2.10.0+cpu`, `torchvision==0.25.0+cpu`). These wheels are hosted by PyTorch, not PyPI, so the `--index-url` flag is required.

**Step 2: Install all remaining dependencies**

```bash
pip install -r requirements.txt
```

Since torch and torchvision are already installed from Step 1, pip will skip them and install everything else from PyPI normally.

> **Why CPU-only?** The app explicitly disables GPU (`gpu=False`) to avoid CUDA DLL conflicts on Windows. A GPU build of PyTorch is not needed and would only cause problems.
>
> **Why two steps?** The `+cpu` suffix on the torch/torchvision versions in `requirements.txt` tells pip to match the exact CPU-only wheel. PyPI doesn't carry these builds — only PyTorch's own index does. Running `pip install -r requirements.txt` alone will fail with a version-not-found error for those two packages.

---

## Running the App

```bat
python main.py
```

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `easyocr` | OCR engine (runs locally, CPU-only) |
| `torch` + `torchvision` | EasyOCR backend (CPU wheel) |
| `PyQt6` | Desktop UI and threading |
| `qt-material` | Dark Material Design theme |
| `opencv-python-headless` | Image preprocessing |
| `Pillow` | Image loading |

Full pinned versions are in `requirements.txt`.

---

## Privacy

All processing happens **on your local machine**:

- Images are read directly from disk and passed to EasyOCR locally
- No network calls are made during OCR
- No data is sent to any external service
- EasyOCR model weights are downloaded once on first run and cached locally — subsequent runs are fully offline

---


## Architecture Notes

- `ocr_backend.py` strips CUDA/NVIDIA/cuDNN/cuFFT/cuBLAS entries from `PATH` and `PYTHONPATH` before spawning the subprocess. This prevents rogue GPU DLLs from crashing EasyOCR even if you have other software (e.g. NVIDIA drivers, Conda) installed.
- A **pre-flight check** (`python -c "print('preflight_ok')"`) is run in the sanitized environment before spawning OCR. If Python itself crashes, a descriptive error is raised immediately.
- The subprocess communicates exclusively via **stdout JSON** (`{"ok": true, "lines": [...]}` or `{"ok": false, "error": "..."}`), so errors are always surfaced rather than lost.

## Features

- **Dark Material Design UI** — modern dark theme with teal accents via qt-material
- **Zero setup OCR** — uses the Windows built-in OCR engine (no ML models to download)
- **Live image preview** — see the loaded image alongside the output
- **Editable output textarea** — review, manually correct, or annotate the extracted text
- **One-click copy** — Copy All button or standard `Ctrl+A` / `Ctrl+C`
- **Character count** — live display of output length
- **Line count report** — status bar shows how many lines were detected after each run
- **Non-blocking processing** — OCR runs on a background thread so the UI stays responsive
- **Detailed logging** — all activity written to `ocr_debug.log` for easy troubleshooting

---

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Open Image] [Paste Image] [Run OCR] [Clear] [Copy All] │
│                                        Engine: EasyOCR      │
├──────────────────────┬──────────────────────────────────┤
│                      │  OCR Output          1,234 chars │
│   Image Preview      │ ┌──────────────────────────────┐ │
│                      │ │                              │ │
│   (scrollable)       │ │  Extracted text appears      │ │
│                      │ │  here, editable and          │ │
│                      │ │  selectable.                 │ │
│                      │ │                              │ │
│                      │ └──────────────────────────────┘ │
├──────────────────────┴──────────────────────────────────┤
│  Status bar — current state / line count / errors        │
└─────────────────────────────────────────────────────────┘
```

---

## How to Use

1. Click **Open Image** and select a file (PNG, JPG, BMP, TIFF, or GIF)
2. The image appears in the left preview panel
3. Click **Run OCR** — a progress indicator shows while the engine works
4. Extracted text fills the right-hand textarea
5. Edit the text if needed, then use **Copy All** (or `Ctrl+A` → `Ctrl+C`) to copy it

6. 
## Troubleshooting

### Subprocess produces no output / crashes on startup

Windows exit codes to look for:

| Code | Meaning |
|---|---|
| `0xC0000005` | Native DLL crash — usually a CUDA/GPU DLL conflict |
| `0xC000007B` | DLL architecture mismatch (32-bit vs 64-bit) |

**Fix:** Make sure you installed using `install.bat` inside a clean venv. Do not install a GPU version of PyTorch.

To diagnose manually, run the subprocess directly:

```bat
python ocr_subprocess.py "path\to\image.png"
```

This prints a JSON result to stdout with any error details.

### `easyocr import failed`

```bat
pip install easyocr
```

### App window appears but OCR never completes

EasyOCR downloads its model weights (~100 MB) on the **first run only**. This requires an internet connection the first time. After that, OCR works fully offline.

---
