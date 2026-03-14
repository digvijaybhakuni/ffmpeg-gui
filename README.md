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

## Requirements

- Python 3.10+
- `ffmpeg` available in your `PATH`

## Run

```bash
python3 app.py
```

## Notes

- Default output file pattern: `original-name-output.ext`
- Default local output folder (when empty): `input-file-folder/output/`
