# FFmpeg GUI Batch Editor/Encoder

Simple desktop GUI for batch video processing with `ffmpeg`.

## Features

- Select multiple video files.
- Process files in a loop (one by one).
- Edit/encode options:
  - codec, CRF, preset, audio bitrate
  - optional trim start/end time
  - optional extra raw ffmpeg arguments
- Output naming with suffix (`-output` by default).
- Output location:
  - choose a custom output directory, or
  - leave blank to auto-create an `output/` directory next to each input file.
- Optional custom path to the `ffmpeg` binary (for example `ffmpeg.exe` on Windows).

## Requirements

- Python 3.10+
- `ffmpeg` available in your `PATH` (or choose a custom ffmpeg executable path in the app)

## Run

```bash
python3 app.py
```

## Notes

- Default output file pattern: `original-name-output.ext`
- Default local output folder (when empty): `input-file-folder/output/`

## GitHub Actions build

A workflow is included at `.github/workflows/build-executable.yml` to package the app as an executable with PyInstaller on Linux, macOS, and Windows.

- Run it manually from the **Actions** tab (`workflow_dispatch`), or
- let it run automatically on pushes to `main` and pull requests.

Each run uploads platform-specific artifacts named:
- `ffmpeg-gui-Linux`
- `ffmpeg-gui-macOS`
- `ffmpeg-gui-Windows`
