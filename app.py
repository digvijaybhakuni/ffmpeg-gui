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

VIDEO_CODEC_OPTIONS = ["libx264", "libx265", "libvpx-vp9", "h264_nvenc", "hevc_nvenc", "copy"]
PRESET_OPTIONS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
AUDIO_BITRATE_OPTIONS = ["96k", "128k", "160k", "192k", "256k", "320k"]


class FFmpegGuiApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FFmpeg Batch GUI")
        self.root.geometry("980x720")
        self.root.minsize(900, 660)

        self.files: list[Path] = []
        self.running = False

        self.output_dir_var = tk.StringVar()
        self.ffmpeg_path_var = tk.StringVar()
        self.codec_var = tk.StringVar(value="libx264")
        self.crf_var = tk.IntVar(value=23)
        self.preset_var = tk.StringVar(value="medium")
        self.audio_bitrate_var = tk.StringVar(value="128k")
        self.suffix_var = tk.StringVar(value="-output")
        self.start_time_var = tk.StringVar()
        self.end_time_var = tk.StringVar()
        self.extra_args_var = tk.StringVar()

        self._configure_style()
        self._build_ui()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.root.configure(bg="#0f172a")

        style.configure("App.TFrame", background="#0f172a")
        style.configure("Card.TLabelframe", background="#111827", foreground="#e5e7eb", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background="#111827", foreground="#93c5fd", font=("TkDefaultFont", 10, "bold"))

        style.configure("App.TLabel", background="#111827", foreground="#e5e7eb")
        style.configure("Hint.TLabel", background="#111827", foreground="#9ca3af", font=("TkDefaultFont", 9))
        style.configure("Title.TLabel", background="#0f172a", foreground="#dbeafe", font=("TkDefaultFont", 15, "bold"))

        style.configure("Accent.TButton", padding=(12, 6), font=("TkDefaultFont", 10, "bold"))
        style.configure("TButton", padding=(10, 5))
        style.configure("TEntry", padding=4)
        style.configure("TCombobox", padding=3)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, style="App.TFrame", padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="FFmpeg Batch Encoder", style="Title.TLabel").pack(anchor="w", pady=(0, 10))

        files_frame = ttk.LabelFrame(container, text="Input Files", style="Card.TLabelframe", padding=12)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        btn_row = ttk.Frame(files_frame, style="App.TFrame")
        btn_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btn_row, text="Add files", command=self.add_files).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="Clear", command=self.clear_files).pack(side=tk.LEFT)

        self.file_list = tk.Listbox(
            files_frame,
            height=8,
            selectmode=tk.EXTENDED,
            bg="#0b1220",
            fg="#e5e7eb",
            selectbackground="#1d4ed8",
            selectforeground="#ffffff",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#1f2937",
            highlightcolor="#2563eb",
        )
        self.file_list.pack(fill=tk.BOTH, expand=True)

        opts = ttk.LabelFrame(container, text="Encoding Options", style="Card.TLabelframe", padding=12)
        opts.pack(fill=tk.X, pady=(0, 10))

        row1 = ttk.Frame(opts, style="App.TFrame")
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="Video codec", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Combobox(row1, textvariable=self.codec_var, values=VIDEO_CODEC_OPTIONS, state="readonly", width=14).pack(
            side=tk.LEFT, padx=(8, 16)
        )

        ttk.Label(row1, text="Preset", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Combobox(row1, textvariable=self.preset_var, values=PRESET_OPTIONS, state="readonly", width=12).pack(
            side=tk.LEFT, padx=(8, 16)
        )

        ttk.Label(row1, text="Audio bitrate", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Combobox(
            row1,
            textvariable=self.audio_bitrate_var,
            values=AUDIO_BITRATE_OPTIONS,
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT, padx=(8, 0))

        row2 = ttk.Frame(opts, style="App.TFrame")
        row2.pack(fill=tk.X, pady=6)
        ttk.Label(row2, text="CRF (0–51)", style="App.TLabel").pack(side=tk.LEFT)
        self.crf_scale = ttk.Scale(row2, from_=0, to=51, variable=self.crf_var, command=self._sync_crf_label)
        self.crf_scale.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        self.crf_label = ttk.Label(row2, text=str(self.crf_var.get()), style="App.TLabel", width=3)
        self.crf_label.pack(side=tk.LEFT)

        row3 = ttk.Frame(opts, style="App.TFrame")
        row3.pack(fill=tk.X, pady=4)
        ttk.Label(row3, text="Trim start (optional)", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.start_time_var, width=16).pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(row3, text="Trim end (optional)", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.end_time_var, width=16).pack(side=tk.LEFT, padx=8)

        row4 = ttk.Frame(opts, style="App.TFrame")
        row4.pack(fill=tk.X, pady=4)
        ttk.Label(row4, text="Output suffix", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Entry(row4, textvariable=self.suffix_var, width=14).pack(side=tk.LEFT, padx=(8, 0))

        row5 = ttk.Frame(opts, style="App.TFrame")
        row5.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(row5, text="Manual ffmpeg flags (single override box)", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Entry(row5, textvariable=self.extra_args_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        ttk.Label(
            opts,
            text="Use the manual box for any extra flags, e.g. -vf scale=1280:-2 -movflags +faststart",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        out = ttk.LabelFrame(container, text="Output", style="Card.TLabelframe", padding=12)
        out.pack(fill=tk.X, pady=(0, 10))

        out_row = ttk.Frame(out, style="App.TFrame")
        out_row.pack(fill=tk.X)
        ttk.Label(out_row, text="Output directory (optional)", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Entry(out_row, textvariable=self.output_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(out_row, text="Browse", command=self.choose_output_dir).pack(side=tk.LEFT)

        ffmpeg_row = ttk.Frame(out, style="App.TFrame")
        ffmpeg_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(ffmpeg_row, text="ffmpeg binary (optional)", style="App.TLabel").pack(side=tk.LEFT)
        ttk.Entry(ffmpeg_row, textvariable=self.ffmpeg_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(ffmpeg_row, text="Browse", command=self.choose_ffmpeg_binary).pack(side=tk.LEFT)

        actions = ttk.Frame(container, style="App.TFrame")
        actions.pack(fill=tk.X, pady=(0, 10))
        self.run_button = ttk.Button(actions, text="Run batch", style="Accent.TButton", command=self.run_batch)
        self.run_button.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(actions, orient="horizontal", mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        log_frame = ttk.LabelFrame(container, text="Log", style="Card.TLabelframe", padding=12)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=11,
            wrap=tk.WORD,
            bg="#0b1220",
            fg="#d1d5db",
            insertbackground="#d1d5db",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#1f2937",
            highlightcolor="#2563eb",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _sync_crf_label(self, _: str) -> None:
        self.crf_label.config(text=str(int(self.crf_var.get())))

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

        crf = str(int(self.crf_var.get()))
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
