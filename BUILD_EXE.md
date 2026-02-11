# How to Build Standalone EXE

This guide explains how to package StreamTune into a single `.exe` file that runs without Python installed.

## Prerequisites
- Python 3.8+ installed.
- VLC installed (and you need the `libvlc.dll` and `libvlccore.dll` + `plugins` folder for full portability).

## Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

## Step 2: Locate VLC Files (Critical for Portability)
To make the EXE work on a machine *without* VLC installed, you must bundle the VLC libraries.

1. Go to your VLC installation folder (usually `C:\Program Files\VideoLAN\VLC`).
2. Copy `libvlc.dll` and `libvlccore.dll` to your project root (same folder as `main.py`).
3. Copy the `plugins` directory from VLC to your project root.

**Structure should look like:**
```
SMP/
  main.py
  core/
  ui/
  libvlc.dll
  libvlccore.dll
  plugins/
```

## Step 3: Run PyInstaller

Use the following command to build the executable. We use `--add-binary` and `--add-data` to bundle VLC and yt-dlp dependencies.

```bash
pyinstaller --noconfirm --onefile --windowed --name "StreamTune" \
    --add-binary "libvlc.dll;." \
    --add-binary "libvlccore.dll;." \
    --add-data "plugins;plugins" \
    --collect-all "yt_dlp" \
    main.py
```

**Explanation of flags:**
- `--onefile`: Bundles everything into a single .exe.
- `--windowed`: Hides the console window.
- `--add-binary`: Includes the critical VLC DLLs.
- `--add-data`: Includes the VLC plugins folder (needed for audio decoders).
- `--collect-all "yt_dlp"`: Ensures all of yt-dlp's internal extractors are included.

## Step 4: Run
The output file will be in the `dist/` folder named `StreamTune.exe`. You can move this file anywhere and run it.

## Troubleshooting
- **Failed to load generic**: This usually means `plugins` folder wasn't found. Ensure `--add-data "plugins;plugins"` is correct.
- **yt_dlp errors**: Ensure `--collect-all "yt_dlp"` was used.
