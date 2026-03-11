# OCR Tool

A lightweight desktop application for extracting text from images using the built-in **Windows.Media.Ocr** engine — no model downloads, no API keys, no internet required.

---

## Goal

Quickly convert any image file into selectable, copyable text. Load an image, click **Run OCR**, and the recognized text appears instantly in the output area ready to copy elsewhere.

---

## Features

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
│  [Open Image]  [Run OCR]  [Clear]    [Copy All]         │
│                                   Engine: Windows.Media.Ocr │
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

---

## Functions

| Function | File | Description |
|---|---|---|
| `MainWindow` | `gui.py` | Builds and manages the entire UI |
| `open_image()` | `gui.py` | Opens a file dialog and loads a preview |
| `run_ocr()` | `gui.py` | Starts the background OCR worker |
| `clear_all()` | `gui.py` | Resets the image, preview, and output |
| `copy_all()` | `gui.py` | Selects all output text and copies to clipboard |
| `OCRWorker.run()` | `worker.py` | Background QThread that calls the OCR backend |
| `run_ocr()` | `ocr_backend.py` | Spawns `ocr_subprocess.py` and parses its JSON result |
| `main()` | `ocr_subprocess.py` | Isolated process that calls `Windows.Media.Ocr` via `winsdk` |

---

## Architecture

The OCR engine runs in an **isolated subprocess** (`ocr_subprocess.py`) to safely handle WinRT async calls and avoid COM conflicts with the Qt event loop. Results are returned as a JSON payload over stdout and parsed by `ocr_backend.py`.

```
gui.py  →  OCRWorker (QThread)  →  ocr_backend.py  →  ocr_subprocess.py
                                                           └── Windows.Media.Ocr
```

---

## Requirements

- **Windows 10 / 11** (Windows.Media.Ocr is Windows-only)
- **Python 3.10+**
- At least one **Windows language pack** installed (e.g. English) for the OCR engine

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python main.py
```

---

## Supported Image Formats

PNG · JPG / JPEG · BMP · TIFF / TIF · GIF

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `winsdk import failed` | winsdk not installed | `pip install winsdk` |
| `OCR engine unavailable` | No language pack | Install English (or your language) in Windows Settings → Time & Language |
| Empty output, no error | Subprocess crashed silently | Check `ocr_debug.log` and run `python ocr_subprocess.py "your_image.png"` directly |