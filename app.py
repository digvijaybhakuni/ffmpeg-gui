import os
import shlex
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


VIDEO_FILETYPES = [
    ("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.flv *.wmv"),
    ("All files", "*.*"),
]


class FFmpegGuiApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FFmpeg Batch GUI")
        self.root.geometry("900x650")

        self.files: list[Path] = []
        self.running = False

        self.output_dir_var = tk.StringVar()
        self.ffmpeg_path_var = tk.StringVar()
        self.codec_var = tk.StringVar(value="libx264")
        self.crf_var = tk.StringVar(value="23")
        self.preset_var = tk.StringVar(value="medium")
        self.audio_bitrate_var = tk.StringVar(value="128k")
        self.suffix_var = tk.StringVar(value="-output")
        self.start_time_var = tk.StringVar()
        self.end_time_var = tk.StringVar()
        self.extra_args_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        files_frame = ttk.LabelFrame(container, text="Input files", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True)

        btn_row = ttk.Frame(files_frame)
        btn_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btn_row, text="Add files", command=self.add_files).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="Clear", command=self.clear_files).pack(side=tk.LEFT)

        self.file_list = tk.Listbox(files_frame, height=8, selectmode=tk.EXTENDED)
        self.file_list.pack(fill=tk.BOTH, expand=True)

        opts = ttk.LabelFrame(container, text="Encoding / editing options", padding=10)
        opts.pack(fill=tk.X, pady=10)

        row1 = ttk.Frame(opts)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="Video codec").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.codec_var, width=18).pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(row1, text="CRF").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.crf_var, width=8).pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(row1, text="Preset").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.preset_var, width=12).pack(side=tk.LEFT, padx=8)

        row2 = ttk.Frame(opts)
        row2.pack(fill=tk.X, pady=4)
        ttk.Label(row2, text="Audio bitrate").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.audio_bitrate_var, width=12).pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(row2, text="Output suffix").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.suffix_var, width=14).pack(side=tk.LEFT, padx=8)

        row3 = ttk.Frame(opts)
        row3.pack(fill=tk.X, pady=4)
        ttk.Label(row3, text="Trim start (optional, e.g. 00:00:05)").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.start_time_var, width=16).pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(row3, text="Trim end (optional)").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.end_time_var, width=16).pack(side=tk.LEFT, padx=8)

        row4 = ttk.Frame(opts)
        row4.pack(fill=tk.X, pady=4)
        ttk.Label(row4, text="Extra ffmpeg args").pack(side=tk.LEFT)
        ttk.Entry(row4, textvariable=self.extra_args_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        out = ttk.LabelFrame(container, text="Output", padding=10)
        out.pack(fill=tk.X)

        out_row = ttk.Frame(out)
        out_row.pack(fill=tk.X)
        ttk.Label(out_row, text="Output directory (optional; leave blank to use each file's folder/output)").pack(
            side=tk.LEFT
        )
        ttk.Entry(out_row, textvariable=self.output_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(out_row, text="Browse", command=self.choose_output_dir).pack(side=tk.LEFT)

        ffmpeg_row = ttk.Frame(out)
        ffmpeg_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(ffmpeg_row, text="ffmpeg binary (optional; leave blank to use PATH)").pack(side=tk.LEFT)
        ttk.Entry(ffmpeg_row, textvariable=self.ffmpeg_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(ffmpeg_row, text="Browse", command=self.choose_ffmpeg_binary).pack(side=tk.LEFT)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=10)
        self.run_button = ttk.Button(actions, text="Run batch", command=self.run_batch)
        self.run_button.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(actions, orient="horizontal", mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        log_frame = ttk.LabelFrame(container, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=12, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def add_files(self) -> None:
        selected = filedialog.askopenfilenames(title="Select video files", filetypes=VIDEO_FILETYPES)
        for f in selected:
            path = Path(f)
            if path not in self.files:
                self.files.append(path)
                self.file_list.insert(tk.END, str(path))

    def remove_selected(self) -> None:
        idxs = list(self.file_list.curselection())
        for i in reversed(idxs):
            del self.files[i]
            self.file_list.delete(i)

    def clear_files(self) -> None:
        self.files.clear()
        self.file_list.delete(0, tk.END)

    def choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="Choose output directory")
        if selected:
            self.output_dir_var.set(selected)

    def choose_ffmpeg_binary(self) -> None:
        filetypes = [("ffmpeg", "ffmpeg ffmpeg.exe"), ("Executable", "*.exe"), ("All files", "*.*")]
        selected = filedialog.askopenfilename(title="Choose ffmpeg binary", filetypes=filetypes)
        if selected:
            self.ffmpeg_path_var.set(selected)

    def _resolve_ffmpeg_binary(self) -> str | None:
        custom = self.ffmpeg_path_var.get().strip()
        if custom:
            custom_path = Path(custom).expanduser()
            if is_executable_file(custom_path):
                return str(custom_path)
            return None

        return shutil_which("ffmpeg")

    def build_command(self, input_file: Path, output_file: Path) -> list[str]:
        ffmpeg_binary = self._resolve_ffmpeg_binary()
        if not ffmpeg_binary:
            raise RuntimeError("Could not resolve ffmpeg binary")

        cmd = [ffmpeg_binary, "-y", "-i", str(input_file)]

        start = self.start_time_var.get().strip()
        end = self.end_time_var.get().strip()
        if start:
            cmd.extend(["-ss", start])
        if end:
            cmd.extend(["-to", end])

        codec = self.codec_var.get().strip()
        if codec:
            cmd.extend(["-c:v", codec])

        crf = self.crf_var.get().strip()
        if crf:
            cmd.extend(["-crf", crf])

        preset = self.preset_var.get().strip()
        if preset:
            cmd.extend(["-preset", preset])

        ab = self.audio_bitrate_var.get().strip()
        if ab:
            cmd.extend(["-b:a", ab])

        extra_args = self.extra_args_var.get().strip()
        if extra_args:
            cmd.extend(shlex.split(extra_args))

        cmd.append(str(output_file))
        return cmd

    def _resolve_output_path(self, input_file: Path) -> Path:
        suffix = self.suffix_var.get().strip() or "-output"
        base_output_dir = self.output_dir_var.get().strip()

        if base_output_dir:
            output_dir = Path(base_output_dir)
        else:
            output_dir = input_file.parent / "output"

        output_dir.mkdir(parents=True, exist_ok=True)

        output_name = f"{input_file.stem}{suffix}{input_file.suffix}"
        return output_dir / output_name

    def run_batch(self) -> None:
        if self.running:
            return

        if not self.files:
            messagebox.showerror("No files", "Please add one or more video files first.")
            return

        ffmpeg_binary = self._resolve_ffmpeg_binary()
        if not ffmpeg_binary:
            messagebox.showerror("ffmpeg missing", "Could not find ffmpeg. Set a custom binary path or add ffmpeg to PATH.")
            return

        self.log(f"Using ffmpeg: {ffmpeg_binary}")

        self.running = True
        self.run_button.config(state=tk.DISABLED)
        self.progress["maximum"] = len(self.files)
        self.progress["value"] = 0

        worker = threading.Thread(target=self._process_files, daemon=True)
        worker.start()

    def _process_files(self) -> None:
        success = 0
        for idx, input_file in enumerate(self.files, start=1):
            output_file = self._resolve_output_path(input_file)
            cmd = self.build_command(input_file, output_file)
            self.log(f"[{idx}/{len(self.files)}] Processing: {input_file.name}")
            self.log("$ " + " ".join(shlex.quote(x) for x in cmd))

            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                success += 1
                self.log(f"✔ Done: {output_file}")
            else:
                self.log(f"✘ Failed ({proc.returncode}): {input_file}")
                if proc.stderr:
                    self.log(proc.stderr.strip())

            self.progress["value"] = idx

        self.log(f"Finished. Success: {success}/{len(self.files)}")
        self.running = False
        self.run_button.config(state=tk.NORMAL)


def shutil_which(binary: str) -> str | None:
    candidates = [binary]
    if os.name == "nt" and not binary.lower().endswith(".exe"):
        candidates.append(f"{binary}.exe")

    for directory in os.environ.get("PATH", "").split(os.pathsep):
        for candidate in candidates:
            path = Path(directory) / candidate
            if is_executable_file(path):
                return str(path)

    return None


def is_executable_file(path: Path) -> bool:
    if not path.is_file():
        return False

    if os.name == "nt":
        return True

    return os.access(path, os.X_OK)


def main() -> None:
    root = tk.Tk()
    app = FFmpegGuiApp(root)
    app.log("Ready. Add video files, adjust options, then click 'Run batch'.")
    root.mainloop()


if __name__ == "__main__":
    main()
