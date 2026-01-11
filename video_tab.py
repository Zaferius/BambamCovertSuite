import os, subprocess, threading, tkinter as tk, tempfile
from tkinter import ttk, filedialog, messagebox
import concurrent.futures, multiprocessing

from PIL import Image, ImageTk, ImageDraw

import localization as i18n

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None

VIDEO_FORMATS = ["Original","MP4","MOV","MKV","AVI","WEBM","GIF"]
MAX_CROP_PREVIEW = (420, 260)

# Windows'ta ffmpeg çağrılarını konsolsuz çalıştırmak için
_NO_WINDOW_KW = (
    {"creationflags": subprocess.CREATE_NO_WINDOW}
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW")
    else {}
)

def get_ffmpeg_cmd():
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, exe)
    if os.path.exists(local):
        return [local]
    return ["ffmpeg"]

def get_ffprobe_cmd():
    exe = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, exe)
    if os.path.exists(local):
        return [local]
    return ["ffprobe"]

def have_ffmpeg():
    try:
        cmd = get_ffmpeg_cmd() + ["-version"]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **_NO_WINDOW_KW)
        return True
    except Exception:
        return False

def build_ffmpeg_cmd(src, out, target, resize_enabled=False, width=1920, height=1080, keep_aspect=True, fps=0):
    if target == "Original":
        cmd = get_ffmpeg_cmd() + ["-y", "-i", src, "-c", "copy", out]
    else:
        ext = target.lower()
        cmd = get_ffmpeg_cmd() + ["-y", "-i", src]
        if resize_enabled:
            w = width; h = height
            if keep_aspect:
                cmd += ["-vf", f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"]
            else:
                cmd += ["-vf", f"scale={w}:{h}"]
        if fps > 0:
            cmd += ["-r", str(fps)]
        vcodec = "libx264" if ext in ("mp4", "mov", "m4v") else ("libvpx-vp9" if ext == "webm" else "libx264")
        acodec = "aac" if ext in ("mp4", "mov", "m4v") else ("libopus" if ext == "webm" else "aac")
        cmd += ["-c:v", vcodec, "-c:a", acodec, out]
    return cmd

def _convert_single_video(params):
    src = params['src']
    output_dir = params['output_dir']
    target = params['target']
    resize_enabled = params['resize_enabled']
    width = params['width']
    height = params['height']
    keep_aspect = params['keep_aspect']
    fps = params['fps']
    delete_original = params.get('delete_original', False)
    
    base = os.path.splitext(os.path.basename(src))[0].replace(os.sep, "_")
    if target == "Original":
        ext = os.path.splitext(src)[1].lstrip(".")
        out = os.path.join(output_dir, f"{base}.{ext}")
    else:
        ext = target.lower()
        out = os.path.join(output_dir, f"{base}.{ext}")
    counter = 1
    while os.path.exists(out):
        name, e = os.path.splitext(out)
        out = f"{name}_{counter}{e}"
        counter += 1
    cmd = build_ffmpeg_cmd(src, out, target, resize_enabled, width, height, keep_aspect, fps)
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **_NO_WINDOW_KW)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "FFmpeg error")
    
    # Delete original if requested and conversion was successful
    if delete_original and os.path.exists(out):
        try:
            os.remove(src)
        except Exception:
            pass

class VideoTab:
    def __init__(self, app, parent):
        self.app=app; self.root=app.root; self.parent=parent
        if not have_ffmpeg():
            messagebox.showwarning(i18n.t("video.ffmpeg.missing_title"), i18n.t("video.ffmpeg.missing_message"))

        self.files=[]; self.output_dir=""
        self.target_format=tk.StringVar(value="MP4")
        self.keep_aspect=tk.BooleanVar(value=True)
        self.resize_enabled=tk.BooleanVar(value=False)
        self.width=tk.IntVar(value=1920); self.height=tk.IntVar(value=1080)
        self.fps=tk.IntVar(value=0)
        
        # Output location settings
        self.mirror_to_source = tk.BooleanVar(value=False)
        self.delete_originals = tk.BooleanVar(value=False)
        self.radio_var = None

        # GIF specific settings (use same W/H/FPS by default)
        self.gif_width=tk.IntVar(value=480)
        self.gif_height=tk.IntVar(value=270)
        self.gif_fps=tk.IntVar(value=12)

        self.is_busy=False
        self.cancel_requested=False
        self.current_proc=None
        self.just_finished=False  # tab change sonrası auto-clear

        # Crop settings (single video only)
        self.crop_settings = {
            "enabled": False,
            "video": None,
            "left": 0,
            "right": 0,
            "top": 0,
            "bottom": 0,
        }
        self._crop_preview_photo = None
        self._crop_preview_image = None
        self._crop_preview_scale = 1.0
        self._crop_preview_display_size = (0, 0)
        self.crop_win = None
        self.crop_canvas = None
        self.crop_canvas_image_id = None
        self.crop_canvas_rect_id = None
        self._crop_sliders_frame = None
        self._crop_slider_widgets = []
        self._crop_timeline_frame = None
        self._crop_timeline_sliders = None
        self.crop_trim_start_scale = None
        self.crop_trim_end_scale = None
        self.crop_trim_status = None
        self.crop_trim_start_label = None
        self.crop_trim_end_label = None
        self.crop_timeline_canvas = None
        self.trim_enable_var = tk.BooleanVar(value=False)
        self.trim_start = tk.DoubleVar(value=0.0)
        self.trim_end = tk.DoubleVar(value=0.0)
        self.trim_duration = 0.0
        self.trim_video = None
        self._is_updating_trim = False

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        pad={"padx":10,"pady":5}
        main=ttk.Frame(self.parent); main.pack(fill="both", expand=True, padx=8, pady=8)
        self.lbl_title = ttk.Label(main, text=i18n.t("video.title"), font=("Segoe UI",12,"bold"))
        self.lbl_title.pack(pady=(0,8))

        self.lf_select = ttk.LabelFrame(main, text=i18n.t("video.section.select")); files=self.lf_select; files.pack(fill="x", **pad)
        self.drop_canvas=tk.Canvas(files, bg=self.app.frame_bg, highlightthickness=0, height=120)
        self.drop_canvas.pack(fill="x", padx=6, pady=6)
        self.drop_canvas.bind("<Configure>", self._draw_drop_zone_border)

        inner = ttk.Frame(self.drop_canvas)
        self.drop_canvas.create_window(10, 10, window=inner, anchor="nw")

        top = ttk.Frame(inner); top.pack(fill="x")

        self.btn_browse = ttk.Button(top, text=i18n.t("video.btn.browse_files"), command=self._select_files)
        self.btn_browse.pack(side="left", padx=(0,8), pady=2)
        self.btn_add_folder = ttk.Button(top, text=i18n.t("video.btn.add_folder"), command=self._add_folders)
        self.btn_add_folder.pack(side="left", padx=(0,8), pady=2)
        self.lbl_count=ttk.Label(top, text=i18n.t("video.files.count", file_count=0)); self.lbl_count.pack(side="left", pady=2)
        self.btn_clear=ttk.Button(top, text=i18n.t("video.btn.clear_selected"), command=self._clear_selected)
        self.btn_clear.pack(side="right", padx=5)

        self.lbl_hint = ttk.Label(
            inner,
            text=i18n.t("video.hint.dragdrop"),
            wraplength=460,
            justify="left",
        )
        self.lbl_hint.pack(fill="x", anchor="w", pady=(6,4))

        # Configure white text style for radio buttons without hover effect
        try:
            style = ttk.Style()
            style.configure("White.TRadiobutton", 
                          foreground=self.app.fg, 
                          background=self.app.frame_bg)
            style.map("White.TRadiobutton",
                     background=[("active", self.app.frame_bg), ("!active", self.app.frame_bg)],
                     foreground=[("active", self.app.fg), ("!active", self.app.fg)])
        except Exception:
            pass

        self.lf_output=ttk.LabelFrame(main, text=i18n.t("video.section.output")); out=self.lf_output; out.pack(fill="x", **pad)
        
        self.radio_var = tk.StringVar(value="mirror" if self.mirror_to_source.get() else "folder")
        
        # radio: use folder (üstte, browse button yanında)
        row1 = ttk.Frame(out); row1.pack(fill="x", padx=6, pady=(6, 2))
        self.rb_folder = ttk.Radiobutton(row1, text=i18n.t("image.output.radio.folder"),
                                         value="folder", variable=self.radio_var,
                                         command=self._on_output_mode_change)
        self.rb_folder.pack(side="left")
        self.rb_folder.configure(style="White.TRadiobutton")
        self.btn_out_browse = ttk.Button(row1, text=i18n.t("video.output.btn.browse"), command=self._select_output)
        self.btn_out_browse.pack(side="left", padx=(12, 8))
        self.lbl_out = ttk.Label(row1, text=i18n.t("video.output.label.not_selected"))
        self.lbl_out.configure(foreground="#c7b2ff")
        self.lbl_out.pack(side="left", padx=(6, 0))
        self.btn_clear_output = ttk.Button(row1, text=i18n.t("video.output.btn.clear"), command=self._clear_output_folder)
        self.btn_clear_output.pack(side="right", padx=6)
        
        # radio: mirror to source (altta)
        row2 = ttk.Frame(out); row2.pack(fill="x", padx=6, pady=(2, 6))
        self.rb_mirror = ttk.Radiobutton(row2, text=i18n.t("image.output.radio.mirror"),
                                         value="mirror", variable=self.radio_var,
                                         command=self._on_output_mode_change)
        self.rb_mirror.pack(side="left")
        self.rb_mirror.configure(style="White.TRadiobutton")
        
        # delete originals
        self.chk_delete_originals = ttk.Checkbutton(out, text=i18n.t("image.output.delete_originals"),
                                                    variable=self.delete_originals)
        self.chk_delete_originals.pack(anchor="w", padx=6, pady=(0, 6))

        self.lf_format=ttk.LabelFrame(main, text=i18n.t("video.section.format")); fmt=self.lf_format; fmt.pack(fill="x", **pad)
        self.lbl_format = ttk.Label(fmt, text=i18n.t("video.format.label")); self.lbl_format.pack(side="left", padx=5, pady=5)
        om=tk.OptionMenu(fmt, self.target_format, *VIDEO_FORMATS, command=self._on_format_change)
        om.pack(side="left", padx=5, pady=5); self._style_optionmenu(om)

        # Resize controls (hidden when Resize unchecked or Original format)
        self.resf=ttk.Frame(fmt); self.resf.pack(side="left", padx=15, pady=5)
        ttk.Checkbutton(self.resf, text=i18n.t("video.resize.enable"), variable=self.resize_enabled,
                        command=self._toggle_resize_controls).pack(side="left")
        self.lbl_w = ttk.Label(self.resf, text=i18n.t("video.resize.width_short")); self.lbl_w.pack(side="left", padx=(10,3))
        self.ent_w=tk.Entry(self.resf, textvariable=self.width, width=6,
                            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"); self.ent_w.pack(side="left")
        self.lbl_h = ttk.Label(self.resf, text=i18n.t("video.resize.height_short")); self.lbl_h.pack(side="left", padx=(8,3))
        self.ent_h=tk.Entry(self.resf, textvariable=self.height, width=6,
                            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"); self.ent_h.pack(side="left")
        ttk.Checkbutton(self.resf, text=i18n.t("video.resize.keep_aspect"), variable=self.keep_aspect).pack(side="left", padx=(10,0))

        self.fpsf=ttk.Frame(fmt); self.fpsf.pack(side="left", padx=15, pady=5)
        self.lbl_fps = ttk.Label(self.fpsf, text=i18n.t("video.fps.label")); self.lbl_fps.pack(side="left", padx=(0,5))
        self.ent_fps=tk.Entry(self.fpsf, textvariable=self.fps, width=5,
                              bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"); self.ent_fps.pack(side="left")

        # GIF settings button (visible only when GIF selected)
        self.btn_gif_settings = ttk.Button(fmt, text=i18n.t("video.gif.btn_settings"), command=self._open_gif_settings)

        # Crop controls
        self.crop_frame = ttk.LabelFrame(main, text=i18n.t("video.crop.section"))
        self.crop_frame.pack(fill="x", padx=8, pady=(0, 10))
        crop_row = ttk.Frame(self.crop_frame)
        crop_row.pack(fill="x", padx=10, pady=6)
        self.btn_crop = ttk.Button(crop_row, text=i18n.t("video.crop.btn_open"), command=self._open_crop_window)
        self.btn_crop.pack(side="left")
        self.lbl_crop_status = ttk.Label(crop_row, text=i18n.t("video.crop.status.off"))
        self.lbl_crop_status.pack(side="left", padx=10)
        self.lbl_crop_notice = ttk.Label(
            self.crop_frame,
            text=i18n.t("video.crop.note.single_only"),
            foreground="#ff6b6b",
        )
        self.lbl_crop_notice.pack(anchor="w", padx=10, pady=(0, 4))
        self._update_crop_button_state()

        self.lf_progress=ttk.LabelFrame(main, text=i18n.t("video.section.progress")); prog=self.lf_progress; prog.pack(fill="x", **pad)
        
        # Individual file progress (yellow bar)
        file_prog_frame = ttk.Frame(prog)
        file_prog_frame.pack(fill="x", padx=10, pady=(4, 1))
        self.lbl_file_prog = ttk.Label(file_prog_frame, text="", font=("", 8))
        self.lbl_file_prog.pack(anchor="w", pady=(0, 1))
        
        # Create custom style for yellow progress bar with increased thickness
        try:
            style = ttk.Style()
            style.configure("Yellow.Horizontal.TProgressbar", 
                          background="#ffd700", 
                          troughcolor="#2b2b2b",
                          thickness=20)
            self.file_progress = ttk.Progressbar(file_prog_frame, mode="determinate", style="Yellow.Horizontal.TProgressbar")
        except Exception:
            self.file_progress = ttk.Progressbar(file_prog_frame, mode="determinate")
        self.file_progress.pack(fill="x", ipady=8)
        
        # Overall progress (main bar)
        overall_prog_frame = ttk.Frame(prog)
        overall_prog_frame.pack(fill="x", padx=10, pady=(3, 4))
        self.lbl_prog=ttk.Label(overall_prog_frame, text=i18n.t("video.progress.initial"), font=("", 8))
        self.lbl_prog.pack(anchor="w", pady=(0, 1))
        self.progress=ttk.Progressbar(overall_prog_frame, mode="determinate")
        self.progress.pack(fill="x", ipady=8)
        
        self.lbl_status=ttk.Label(prog, text=i18n.t("video.status.idle")); self.lbl_status.pack(pady=(2,4))

        act=ttk.Frame(main); act.pack(pady=10)
        self.btn_start=ttk.Button(act, text=i18n.t("video.btn.start"), command=self._start)
        self.btn_start.pack(side="left", padx=6)

        if DND_FILES:
            try:
                self.drop_canvas.drop_target_register(DND_FILES)
                self.drop_canvas.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

        self._on_format_change(self.target_format.get())

    def _style_optionmenu(self, om):
        om.config(bg=self.app.entry_bg, fg=self.app.fg,
                  activebackground=self.app.button_hover, activeforeground=self.app.fg,
                  highlightthickness=1, highlightbackground=self.app.border,
                  relief="flat", font=self.app.title_font)
        om["menu"].config(bg=self.app.entry_bg, fg=self.app.fg,
                          activebackground=self.app.button_hover, activeforeground=self.app.fg,
                          font=self.app.title_font)

    def _draw_drop_zone_border(self, event):
        self.drop_canvas.delete("border"); m=4
        self.drop_canvas.create_rectangle(m,m,event.width-m,event.height-m,
                                          outline=self.app.fg, dash=(4,3),
                                          width=1, tags="border")

    # ---------------- Selectors ----------------
    def _on_drop(self, event):
        paths=self.root.splitlist(event.data)
        new_files = []
        for p in paths:
            p=p.strip()
            if os.path.isdir(p):
                # Recursively scan folder for video files
                for rootdir, _, files in os.walk(p):
                    for name in files:
                        fp = os.path.join(rootdir, name)
                        if os.path.isfile(fp) and self._is_video_file(fp):
                            new_files.append(fp)
            elif os.path.isfile(p) and self._is_video_file(p):
                new_files.append(p)
        
        if new_files:
            self.files = list(dict.fromkeys(self.files + new_files))
            self.lbl_count.config(text=i18n.t("video.files.count", file_count=len(self.files)))
            self._handle_selection_change()

    def _is_video_file(self, path):
        """Check if file is a video file based on extension"""
        ext = os.path.splitext(path)[1].lower()
        return ext in [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".ts", ".flv", ".wmv", ".mpeg", ".mpg"]
    
    def _select_files(self):
        paths=filedialog.askopenfilenames(
            title=i18n.t("video.section.select"),
            filetypes=[(i18n.t("tabs.video"),"*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.ts")]
        )
        if paths:
            self.files=list(dict.fromkeys(self.files + list(paths)))
            self.lbl_count.config(text=i18n.t("video.files.count", file_count=len(self.files)))
        self._handle_selection_change()
    
    def _add_folders(self):
        """Add folders and scan for video files recursively"""
        folders = []
        while True:
            d = filedialog.askdirectory(title=i18n.t("video.section.select"))
            if not d:
                break
            folders.append(d)
            if not messagebox.askyesno("Add another folder?", "Do you want to add another folder?"):
                break
        
        if not folders:
            return
        
        new_files = []
        for folder in folders:
            for rootdir, _, files in os.walk(folder):
                for name in files:
                    fp = os.path.join(rootdir, name)
                    if os.path.isfile(fp) and self._is_video_file(fp):
                        new_files.append(fp)
        
        if new_files:
            self.files = list(dict.fromkeys(self.files + new_files))
            self.lbl_count.config(text=i18n.t("video.files.count", file_count=len(self.files)))
            self._handle_selection_change()

    def _select_output(self):
        d=filedialog.askdirectory(title=i18n.t("video.section.output"))
        if d:
            self.output_dir=d
            short = d if len(d) <= 45 else "..." + d[-45:]
            self.lbl_out.config(text=short, foreground=self.app.fg)
        self._update_trim_status_label()
    
    def _on_output_mode_change(self):
        use_mirror = (self.radio_var.get() == "mirror")
        self.mirror_to_source.set(use_mirror)
        state = "disabled" if use_mirror else "normal"
        self.btn_out_browse.configure(state=state)
        self.btn_clear_output.configure(state=state)
        
        if use_mirror:
            self.lbl_out.pack_forget()
        else:
            if not self.lbl_out.winfo_ismapped():
                self.lbl_out.pack(side="left", padx=(6, 0))
            if self.output_dir:
                text = self.output_dir if len(self.output_dir) <= 45 else "..." + self.output_dir[-45:]
                self.lbl_out.configure(text=text, foreground=self.app.fg)
            else:
                self.lbl_out.configure(text=i18n.t("video.output.label.not_selected"), foreground="#c7b2ff")

    def _handle_selection_change(self):
        self._update_crop_button_state()
        self._update_trim_for_selection()

    # ---------------- Start / Cancel ----------------
    def _start(self):
        if self.is_busy: return
        if not self.files:
            messagebox.showwarning(i18n.t("video.warning.title"),i18n.t("video.warning.no_files")); return
        
        # Check output dir requirement based on mirror mode
        if not self.mirror_to_source.get() and not self.output_dir:
            messagebox.showwarning(i18n.t("video.warning.title"),i18n.t("video.warning.no_output")); return

        self.is_busy=True
        self.cancel_requested=False
        self.current_proc=None
        self.btn_start.config(state="disabled")
        self.btn_clear.config(state="disabled")
        self.progress["value"]=0
        self.file_progress["value"]=0
        self.lbl_prog.config(text=f"Overall: 0 / {len(self.files)}")
        self.lbl_file_prog.config(text="")
        self.lbl_status.config(text=i18n.t("video.status.processing"))
        
        # Determine output directory for each file
        self.params_list = []
        for s in self.files:
            if self.mirror_to_source.get():
                out_dir = os.path.dirname(s)
            else:
                out_dir = self.output_dir
            self.params_list.append({
                'src': s,
                'output_dir': out_dir,
                'target': self.target_format.get(),
                'resize_enabled': self.resize_enabled.get(),
                'width': self.width.get(),
                'height': self.height.get(),
                'keep_aspect': self.keep_aspect.get(),
                'fps': self.fps.get(),
                'delete_original': self.delete_originals.get()
            })
        threading.Thread(target=self._worker, daemon=True).start()

    def _cancel(self):
        if not self.is_busy: return
        self.cancel_requested=True
        self.lbl_status.config(text=i18n.t("video.status.cancelling"))
        # aktif ffmpeg varsa öldür
        try:
            if self.current_proc and self.current_proc.poll() is None:
                self.current_proc.terminate()
        except Exception:
            pass

    # ---------------- Worker ----------------
    def _worker(self):
        total=len(self.files); done=0; target=self.target_format.get()
        for src in self.files:
            if self.cancel_requested: break
            try:
                base=os.path.splitext(os.path.basename(src))[0].replace(os.sep,"_")
                if target=="Original":
                    ext=os.path.splitext(src)[1].lstrip(".").lower()
                    out=self._avoid_overwrite(os.path.join(self.output_dir, f"{base}.{ext}"))
                    cmd = get_ffmpeg_cmd() + ["-y","-i",src,"-c","copy",out]
                else:
                    ext=target.lower()
                    out=self._avoid_overwrite(os.path.join(self.output_dir, f"{base}.{ext}"))

                    if ext == "gif":
                        # Build simple GIF pipeline using gif settings
                        w = self.gif_width.get() or self.width.get()
                        h = self.gif_height.get() or self.height.get()
                        f = self.gif_fps.get() or max(1, self.fps.get() or 12)
                        filters = []
                        crop_filter = self._get_crop_filter_for(src)
                        if crop_filter:
                            filters.append(crop_filter)
                        if w > 0 and h > 0:
                            filters.append(f"scale={w}:{h}:flags=lanczos")
                        if f > 0:
                            filters.insert(0, f"fps={f}")
                        trim_args = self._build_trim_args(src)
                        cmd = get_ffmpeg_cmd() + ["-y"] + trim_args + ["-i", src]
                        if filters:
                            cmd += ["-vf", ",".join(filters)]
                        cmd += ["-loop", "0", out]
                    else:
                        trim_args = self._build_trim_args(src)
                        cmd = get_ffmpeg_cmd() + ["-y"] + trim_args + ["-i",src]
                        filter_parts = []
                        crop_filter = self._get_crop_filter_for(src)
                        if crop_filter:
                            filter_parts.append(crop_filter)
                        if self.resize_enabled.get():
                            w=self.width.get(); h=self.height.get()
                            if self.keep_aspect.get():
                                filter_parts.append(f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2")
                            else:
                                filter_parts.append(f"scale={w}:{h}")
                        if filter_parts:
                            cmd+=["-vf", ",".join(filter_parts)]
                        if self.fps.get()>0: cmd+=["-r", str(self.fps.get())]
                        vcodec="libx264" if ext in ("mp4","mov","m4v") else ("libvpx-vp9" if ext=="webm" else "libx264")
                        acodec="aac" if ext in ("mp4","mov","m4v") else ("libopus" if ext=="webm" else "aac")
                        cmd+=["-c:v", vcodec, "-c:a", acodec, out]

                # Update file progress label
                self.root.after(0, lambda f=os.path.basename(src): self.lbl_file_prog.config(text=f"Processing: {f}"))
                self.root.after(0, lambda: self.file_progress.config(value=0))
                
                # Get video duration for progress calculation
                duration = self._get_video_duration(src)
                
                # Popen ile başlat -> iptal edilebilir
                self.current_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    **_NO_WINDOW_KW,
                )
                
                # Monitor ffmpeg progress
                if duration > 0:
                    self._monitor_ffmpeg_progress(self.current_proc, duration)
                else:
                    self.current_proc.communicate()
                
                rc = self.current_proc.returncode
                if self.cancel_requested:
                    break
                if rc != 0:
                    raise RuntimeError("ffmpeg error")

            except Exception as e:
                # iptal değilse göster
                if not self.cancel_requested:
                    self.root.after(0, lambda s=os.path.basename(src), er=e:
                        messagebox.showwarning("Error", f"Failed: {s}\n{er}"))
            finally:
                self.current_proc=None
                done+=1
                self.root.after(0, self._tick, done, total)

        self.root.after(0, self._finish, self.cancel_requested)

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe"""
        try:
            cmd = get_ffprobe_cmd() + [
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **_NO_WINDOW_KW)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return 0.0
    
    def _monitor_ffmpeg_progress(self, process, total_duration: float):
        """Monitor ffmpeg stderr output and update file progress bar"""
        import re
        time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
        
        while True:
            if self.cancel_requested:
                break
            
            line = process.stderr.readline()
            if not line:
                if process.poll() is not None:
                    break
                continue
            
            # Parse time from ffmpeg output
            match = time_pattern.search(line)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = float(match.group(3))
                current_time = hours * 3600 + minutes * 60 + seconds
                
                # Calculate percentage
                if total_duration > 0:
                    percentage = min(100, (current_time / total_duration) * 100)
                    self.root.after(0, lambda p=percentage: self.file_progress.config(value=p))
        
        # Ensure we read remaining output
        process.communicate()
        # Set to 100% when done
        self.root.after(0, lambda: self.file_progress.config(value=100))
    
    def _tick(self, done, total):
        self.progress["value"]=(done/total)*100
        self.lbl_prog.config(text=f"Overall: {done} / {total}")

    def _finish(self, cancelled):
        self.is_busy=False
        self.btn_start.config(state="normal")
        self.btn_clear.config(state="normal")
        if cancelled:
            self.lbl_status.config(text=i18n.t("video.status.cancelled"))
        else:
            self.lbl_status.config(text=i18n.t("video.status.completed"))
            self.just_finished=True  # sonraki girişte temizle

    def _finish_with_errors(self, cancelled, total, errors):
        self.is_busy=False
        self.btn_start.config(state="normal")
        self.btn_clear.config(state="normal")
        if cancelled:
            self.lbl_status.config(text=i18n.t("video.status.cancelled"))
        elif errors:
            self.lbl_status.config(text=i18n.t("video.status.completed_errors"))
            msg = i18n.t(
                "video.result.errors_message",
                failed=len(errors),
                total=total,
                path=errors[0][0],
                error=errors[0][1],
            )
            messagebox.showwarning(i18n.t("video.result.errors_title"), msg)
        else:
            self.lbl_status.config(text=i18n.t("video.status.completed"))
            messagebox.showinfo(i18n.t("video.result.done_title"), i18n.t("video.result.done_message", total=total))
            self.just_finished=True

    # ---------------- Helpers / Clear ----------------
    def on_tab_shown(self):
        """Ana notebook tab değişiminde çağrılır."""
        if not self.is_busy and self.just_finished:
            self._clear_all()
            self.just_finished=False

    def _clear_selected(self):
        if self.is_busy: return
        self.files=[]
        self.lbl_count.config(text=i18n.t("video.files.count", file_count=0))
        self._handle_selection_change()

    def _clear_all(self):
        if self.is_busy:
            # güvenlik: Clear'a basılırsa iptal et
            self._cancel()
            return
        self._clear_selected()
        self.output_dir=""
        self.lbl_out.config(text=i18n.t("video.output.label.not_selected"), foreground="#c7b2ff")
        self.progress["value"]=0
        self.file_progress["value"]=0
        self.lbl_prog.config(text=i18n.t("video.progress.initial"))
        self.lbl_file_prog.config(text="")
        self.lbl_status.config(text=i18n.t("video.status.idle"))

    def _clear_output_folder(self):
        if not self.output_dir or not os.path.isdir(self.output_dir):
            messagebox.showinfo(i18n.t("video.info.title"),i18n.t("video.info.output_not_set")); return
        if not messagebox.askyesno(i18n.t("video.clear_output.confirm_title"),i18n.t("video.clear_output.confirm_message")): return
        cnt=0
        for n in os.listdir(self.output_dir):
            p=os.path.join(self.output_dir,n)
            if os.path.isfile(p):
                try: os.remove(p); cnt+=1
                except: pass
        messagebox.showinfo(i18n.t("video.clear_output.done_title"), i18n.t("video.clear_output.done_message", count=cnt))

    def _on_format_change(self, value):
        original=(value=="Original")
        state="disabled" if original else "normal"
        for w in (self.ent_w, self.ent_h, self.ent_fps): w.configure(state=state)
        if original: self.resize_enabled.set(False)
        # GIF settings button visibility
        if value == "GIF":
            self.btn_gif_settings.pack(side="left", padx=15, pady=5)
        else:
            self.btn_gif_settings.pack_forget()
        self._toggle_resize_controls()

    def _toggle_resize_controls(self):
        # Show/hide resize + fps frames depending on checkbox and format
        can_resize = (self.target_format.get() != "Original")
        show = self.resize_enabled.get() and can_resize

        if show:
            self.resf.pack(side="left", padx=15, pady=5)
            self.fpsf.pack(side="left", padx=15, pady=5)
        else:
            self.resf.pack_forget()
            self.fpsf.pack_forget()

        st="normal" if show else "disabled"
        for w in (self.ent_w, self.ent_h, self.ent_fps): w.configure(state=st)

    def _open_gif_settings(self):
        if hasattr(self, "gif_win") and self.gif_win is not None and tk.Toplevel.winfo_exists(self.gif_win):
            self.gif_win.lift()
            return

        self.gif_win = tk.Toplevel(self.root)
        self.gif_win.title(i18n.t("video.gif.window_title"))
        try:
            self.gif_win.configure(bg=self.app.root_bg)
        except Exception:
            pass

        frm = ttk.Frame(self.gif_win)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        # Width / Height
        row1 = ttk.Frame(frm); row1.pack(fill="x", pady=5)
        ttk.Label(row1, text=i18n.t("video.gif.width")).pack(side="left", padx=(0,5))
        ent_w = tk.Entry(row1, textvariable=self.gif_width,
                         bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat")
        ent_w.pack(side="left", padx=(0,10))
        ttk.Label(row1, text=i18n.t("video.gif.height")).pack(side="left", padx=(0,5))
        ent_h = tk.Entry(row1, textvariable=self.gif_height,
                         bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat")
        ent_h.pack(side="left")

        # FPS
        row2 = ttk.Frame(frm); row2.pack(fill="x", pady=5)
        ttk.Label(row2, text=i18n.t("video.gif.fps")).pack(side="left", padx=(0,5))
        ent_fps = tk.Entry(row2, textvariable=self.gif_fps,
                           bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat", width=6)
        ent_fps.pack(side="left")

        # Actions
        act = ttk.Frame(frm); act.pack(fill="x", pady=(10,0))
        ttk.Button(act, text=i18n.t("video.gif.btn.save"), command=self._save_gif_settings).pack(side="right", padx=5)
        ttk.Button(act, text=i18n.t("video.gif.btn.cancel"), command=self.gif_win.destroy).pack(side="right", padx=5)

    def _save_gif_settings(self):
        # Apply GIF settings into main width/height/fps and enable resize
        try:
            w = max(1, int(self.gif_width.get()))
            h = max(1, int(self.gif_height.get()))
            f = max(1, int(self.gif_fps.get()))
        except Exception:
            messagebox.showwarning(i18n.t("video.gif.warning.title"), i18n.t("video.gif.warning.message"))
            return

        self.width.set(w)
        self.height.set(h)
        self.fps.set(f)
        self.resize_enabled.set(True)
        self._toggle_resize_controls()

        if hasattr(self, "gif_win") and self.gif_win is not None:
            self.gif_win.destroy()
            self.gif_win = None

    # ------------- Crop helpers -------------
    def _update_crop_button_state(self):
        single = len(self.files) == 1
        state = "normal" if single else "disabled"
        self.btn_crop.config(state=state)
        notice = i18n.t("video.crop.note.single_only") if single else i18n.t("video.crop.note.disabled")
        color = self.app.fg if single else "#ff6b6b"
        self.lbl_crop_notice.config(text=notice, foreground=color)
        if not single:
            self._clear_crop_settings()
        self._update_crop_status_label()

    def _update_crop_status_label(self):
        cfg = self.crop_settings
        if cfg.get("enabled"):
            txt = i18n.t(
                "video.crop.status.on",
                area=f"L{cfg.get('left',0)}% R{cfg.get('right',0)}% "
                     f"T{cfg.get('top',0)}% B{cfg.get('bottom',0)}%",
            )
        else:
            txt = i18n.t("video.crop.status.off")
        self.lbl_crop_status.config(text=txt)

    def _open_crop_window(self):
        if len(self.files) != 1:
            return
        if self.target_format.get() == "Original":
            messagebox.showwarning(
                i18n.t("video.crop.warning.original_title"),
                i18n.t("video.crop.warning.original_message"),
            )
            return
        video = self.files[0]
        if hasattr(self, "crop_win") and self.crop_win is not None and tk.Toplevel.winfo_exists(self.crop_win):
            self.crop_win.lift()
            return
        if not self._load_crop_preview(video):
            messagebox.showwarning(i18n.t("video.crop.window.title"), i18n.t("video.crop.preview.error"))
            return

        self.crop_win = tk.Toplevel(self.root)
        self.crop_win.title("Crop Tool")
        self.crop_win.geometry("700x400")
        self.crop_win.resizable(False, False)
        self.crop_win.protocol("WM_DELETE_WINDOW", self._close_crop_window)
        try:
            self.crop_win.configure(bg=self.app.root_bg)
        except Exception:
            pass

        cfg = self.crop_settings
        is_active = cfg.get("enabled") and cfg.get("video") == video
        self.crop_enable_var = tk.BooleanVar(value=is_active)
        self.crop_left_var = tk.IntVar(value=cfg.get("left", 0))
        self.crop_right_var = tk.IntVar(value=cfg.get("right", 0))
        self.crop_top_var = tk.IntVar(value=cfg.get("top", 0))
        self.crop_bottom_var = tk.IntVar(value=cfg.get("bottom", 0))

        wrap = ttk.Frame(self.crop_win)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)

        crop_header = ttk.Frame(wrap)
        crop_header.pack(fill="x", pady=(0, 8))
        ttk.Checkbutton(
            crop_header,
            text=i18n.t("video.crop.window.enable"),
            variable=self.crop_enable_var,
            command=self._on_crop_enable_toggle,
        ).pack(side="left")

        body = ttk.Frame(wrap)
        body.pack(fill="both", expand=True)

        # Left: preview (scaled)
        preview_frame = ttk.Frame(body)
        preview_frame.pack(side="left", padx=(0, 10))
        self.crop_preview_label = ttk.Label(preview_frame, relief="solid")
        self.crop_preview_label.pack()
        self._render_crop_preview()

        # Right: sliders stacked vertically
        sliders = ttk.Frame(body)
        sliders.pack(side="left", fill="y")
        self._crop_slider_widgets = []
        self._crop_slider_widgets.append(self._add_crop_slider(sliders, i18n.t("video.crop.slider.left"), self.crop_left_var))
        self._crop_slider_widgets.append(self._add_crop_slider(sliders, i18n.t("video.crop.slider.right"), self.crop_right_var))
        self._crop_slider_widgets.append(self._add_crop_slider(sliders, i18n.t("video.crop.slider.top"), self.crop_top_var))
        self._crop_slider_widgets.append(self._add_crop_slider(sliders, i18n.t("video.crop.slider.bottom"), self.crop_bottom_var))
        self._crop_sliders_frame = sliders

        self._set_crop_controls_state(self.crop_enable_var.get())

        actions = ttk.Frame(wrap)
        actions.pack(fill="x", pady=(6, 0))
        ttk.Button(actions, text=i18n.t("video.crop.btn.reset"), command=self._reset_crop_settings).pack(side="right", padx=4)
        ttk.Button(actions, text=i18n.t("video.crop.btn.apply"), command=self._apply_crop_settings).pack(side="right", padx=4)

    def _close_crop_window(self):
        if hasattr(self, "crop_win") and self.crop_win is not None:
            try:
                self.crop_win.destroy()
            except Exception:
                pass
        self.crop_win = None
        self.crop_canvas = None
        self.crop_canvas_image_id = None
        self.crop_canvas_rect_id = None
        self._crop_sliders_frame = None
        self._crop_timeline_frame = None
        self._crop_slider_widgets = []
        self.crop_trim_start_scale = None
        self.crop_trim_end_scale = None
        self.crop_trim_status = None
        self.crop_timeline_canvas = None
        self._crop_timeline_sliders = None

    def _add_crop_slider(self, parent, label, var):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=4)
        ttk.Label(frame, text=label, width=10).pack(side="left")
        scale = tk.Scale(
            frame,
            from_=0,
            to=40,
            orient="horizontal",
            resolution=1,
            showvalue=True,
            variable=var,
            command=lambda _=None: self._on_crop_slider_change(),
            length=180,
        )
        scale.pack(side="left", padx=6)

    def _load_crop_preview(self, video_path: str) -> bool:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        cmd = get_ffmpeg_cmd() + ["-y", "-ss", "00:00:01", "-i", video_path, "-frames:v", "1", tmp.name]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **_NO_WINDOW_KW)
            if result.returncode != 0:
                return False
            img = Image.open(tmp.name)
            self._crop_preview_image = img.copy()
            return True
        except Exception:
            return False
        finally:
            try:
                os.remove(tmp.name)
            except Exception:
                pass

    def _render_crop_preview(self):
        if self._crop_preview_image is None or not hasattr(self, "crop_preview_label"):
            return
        img = self._crop_preview_image.copy()
        max_w, max_h = MAX_CROP_PREVIEW
        w, h = img.size
        scale = min(max_w / w, max_h / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)
        if scale != 1.0:
            img = img.resize((new_w, new_h), Image.LANCZOS)
        draw = ImageDraw.Draw(img)
        # overlay rectangle according to current sliders
        left = new_w * self.crop_left_var.get() / 100
        right = new_w * (1 - self.crop_right_var.get() / 100)
        top = new_h * self.crop_top_var.get() / 100
        bottom = new_h * (1 - self.crop_bottom_var.get() / 100)
        right = max(left + 5, right)
        bottom = max(top + 5, bottom)
        draw.rectangle([left, top, right, bottom], outline="#ff6b6b", width=2)
        self._crop_preview_scale = scale
        self._crop_preview_display_size = (new_w, new_h)
        self._crop_preview_photo = ImageTk.PhotoImage(img)
        self.crop_preview_label.config(image=self._crop_preview_photo)

    def _draw_crop_rectangle(self):
        # preserved for compatibility; re-render instead
        self._render_crop_preview()

    def _on_crop_slider_change(self):
        self._render_crop_preview()
    
    def _render_timeline_preview(self, video_path: str):
        """Render visual timeline with frame thumbnails"""
        if not hasattr(self, "crop_timeline_canvas") or not self.crop_timeline_canvas:
            return
        
        canvas = self.crop_timeline_canvas
        canvas.delete("all")
        
        # Get canvas width
        canvas.update_idletasks()
        width = canvas.winfo_width()
        if width < 50:
            width = 400
        
        height = 60
        duration = self.trim_duration if self.trim_duration > 0 else 60
        
        # Draw background
        canvas.create_rectangle(0, 0, width, height, fill="#1e1e1e", outline="")
        
        # Extract 8 thumbnails across the video duration
        num_thumbs = 8
        thumb_width = width // num_thumbs
        thumb_height = height - 10
        
        for i in range(num_thumbs):
            timestamp = (i / (num_thumbs - 1)) * duration if num_thumbs > 1 else 0
            x_pos = i * thumb_width + 2
            
            # Draw placeholder rectangles for thumbnails
            canvas.create_rectangle(
                x_pos, 5, x_pos + thumb_width - 4, height - 5,
                fill="#3a3a3a", outline="#555", width=1
            )
            
            # Draw time marker
            time_text = f"{int(timestamp // 60)}:{int(timestamp % 60):02d}"
            canvas.create_text(
                x_pos + thumb_width // 2, height - 2,
                text=time_text, fill="#888", font=("", 7), anchor="s"
            )
        
        # Draw trim markers if enabled
        self._update_timeline_markers()

    def _update_timeline_markers(self):
        """Draw trim start/end markers on timeline canvas"""
        if not hasattr(self, "crop_timeline_canvas") or not self.crop_timeline_canvas:
            return
        
        canvas = self.crop_timeline_canvas
        canvas.delete("marker")
        
        if not self.trim_enable_var.get():
            return
        
        canvas.update_idletasks()
        width = canvas.winfo_width()
        if width < 50:
            width = 400
        height = 60
        duration = self.trim_duration if self.trim_duration > 0 else 60
        
        if duration <= 0:
            return
        
        # Calculate marker positions
        start_pos = (self.trim_start.get() / duration) * width
        end_pos = (self.trim_end.get() / duration) * width
        
        # Draw selection overlay
        canvas.create_rectangle(
            start_pos, 0, end_pos, height,
            fill="#4a90e2", outline="", stipple="gray50", tags="marker"
        )
        
        # Draw start marker
        canvas.create_line(
            start_pos, 0, start_pos, height,
            fill="#00ff00", width=2, tags="marker"
        )
        canvas.create_polygon(
            start_pos - 5, 0, start_pos + 5, 0, start_pos, 8,
            fill="#00ff00", outline="", tags="marker"
        )
        
        # Draw end marker
        canvas.create_line(
            end_pos, 0, end_pos, height,
            fill="#ff0000", width=2, tags="marker"
        )
        canvas.create_polygon(
            end_pos - 5, 0, end_pos + 5, 0, end_pos, 8,
            fill="#ff0000", outline="", tags="marker"
        )
    
    def _on_crop_trim_slider_change(self):
        if hasattr(self, "crop_trim_start_scale") and hasattr(self, "crop_trim_end_scale"):
            self.trim_start.set(float(self.crop_trim_start_scale.get()))
            self.trim_end.set(float(self.crop_trim_end_scale.get()))
            if self.trim_start.get() >= self.trim_end.get():
                self.trim_end.set(self.trim_start.get() + 0.1)
                self.crop_trim_end_scale.set(self.trim_end.get())
        self.trim_enable_var.set(True)
        self._update_timeline_markers()
        self._update_crop_trim_status_label()
        self._update_trim_status_label()

    def _update_crop_trim_status_label(self):
        if not hasattr(self, "crop_trim_status"):
            return
        if not self.trim_enable_var.get():
            self.crop_trim_status.config(text=i18n.t("video.trim.status.off"))
        else:
            self.crop_trim_status.config(
                text=i18n.t(
                    "video.trim.status.on",
                    start=f"{self.trim_start.get():.2f}s",
                    end=f"{self.trim_end.get():.2f}s",
                )
            )

    def _set_crop_controls_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        # show/hide crop sliders
        if self._crop_sliders_frame is not None:
            if enabled:
                self._crop_sliders_frame.pack(side="left", fill="y")
            else:
                self._crop_sliders_frame.pack_forget()
        for widget in getattr(self, "_crop_slider_widgets", []):
            try:
                widget.configure(state=state)
            except Exception:
                pass
        self._render_crop_preview()

    # ------------- Trim helpers -------------
    def _on_trim_toggle(self):
        if self.target_format.get() == "Original" and self.trim_enable_var.get():
            messagebox.showwarning(
                i18n.t("video.trim.warning.original_title"),
                i18n.t("video.trim.warning.original_message"),
            )
            self.trim_enable_var.set(False)
        self._update_trim_controls()
        self._update_timeline_markers()
        self._update_crop_trim_status_label()

    def _on_trim_slider_change(self):
        if self._is_updating_trim:
            return
        start = float(self.trim_start_scale.get())
        end = float(self.trim_end_scale.get())
        if start >= end:
            # keep last valid; snap end just above start
            end = start + 0.1
            self._is_updating_trim = True
            self.trim_end_scale.set(end)
            self._is_updating_trim = False
        self.trim_start.set(start)
        self.trim_end.set(end)
        self._update_trim_status_label()

    def _update_trim_controls(self, initial=False):
        # Trim UI sadece crop penceresinde mevcut; yoksa çık
        if not hasattr(self, "crop_trim_start_scale"):
            return
        single = len(self.files) == 1
        enabled = single and self.target_format.get() != "Original"
        if not enabled:
            self.trim_enable_var.set(False)
        if single and (initial or self.trim_video != self.files[0]):
            self._fetch_trim_duration(self.files[0])
        self._set_crop_controls_state(enabled)

    def _update_trim_status_label(self):
        # Ana sekmede trim gösterilmiyor; crop penceresindeki etiket güncelleniyor
        self._update_crop_trim_status_label()

    def _update_trim_for_selection(self):
        if len(self.files) != 1:
            self.trim_duration = 0.0
            self.trim_video = None
            self.trim_enable_var.set(False)
            self.trim_start.set(0.0)
            self.trim_end.set(0.0)
            if hasattr(self, "crop_trim_start_scale"):
                self.crop_trim_start_scale.set(0.0)
            if hasattr(self, "crop_trim_end_scale"):
                self.crop_trim_end_scale.set(0.0)
        self._update_trim_controls()

    def _fetch_trim_duration(self, video, skip_widget_update=False):
        self.trim_video = video
        self.trim_duration = 0.0
        try:
            cmd = get_ffprobe_cmd() + [
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video,
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **_NO_WINDOW_KW)
            if res.returncode == 0:
                dur = float(res.stdout.strip())
                if dur > 0:
                    self.trim_duration = dur
        except Exception:
            self.trim_duration = 0.0

        if self.trim_duration > 0:
            self._is_updating_trim = True
            if not skip_widget_update:
                if hasattr(self, "crop_trim_start_scale") and self.crop_trim_start_scale:
                    self.crop_trim_start_scale.configure(from_=0, to=self.trim_duration, resolution=0.1)
                    self.crop_trim_start_scale.set(0.0)
                if hasattr(self, "crop_trim_end_scale") and self.crop_trim_end_scale:
                    self.crop_trim_end_scale.configure(from_=0.1, to=self.trim_duration, resolution=0.1)
                    self.crop_trim_end_scale.set(self.trim_duration)
            self.trim_start.set(0.0)
            self.trim_end.set(self.trim_duration)
            self._is_updating_trim = False
        else:
            self.trim_enable_var.set(False)
        self._update_trim_status_label()

    def _build_trim_args(self, src: str):
        if (
            not self.trim_enable_var.get()
            or len(self.files) != 1
            or src != self.files[0]
            or self.target_format.get() == "Original"
        ):
            return []
        start = max(0.0, float(self.trim_start.get()))
        end = max(start, float(self.trim_end.get()))
        if end <= start:
            return []
        return ["-ss", f"{start}", "-to", f"{end}"]

    def _on_crop_enable_toggle(self):
        enabled = self.crop_enable_var.get()
        self._set_crop_controls_state(enabled)
        if enabled and len(self.files) == 1:
            self._render_crop_preview()
        else:
            self.trim_enable_var.set(False)
            self._update_crop_trim_status_label()

    def _apply_crop_settings(self):
        if len(self.files) != 1:
            self._close_crop_window()
            return
        if self.crop_enable_var.get() and self.target_format.get() == "Original":
            messagebox.showwarning(
                i18n.t("video.crop.warning.original_title"),
                i18n.t("video.crop.warning.original_message"),
            )
            return
        video = self.files[0]
        if self.crop_enable_var.get():
            self.crop_settings.update(
                {
                    "enabled": True,
                    "video": video,
                    "left": int(self.crop_left_var.get()),
                    "right": int(self.crop_right_var.get()),
                    "top": int(self.crop_top_var.get()),
                    "bottom": int(self.crop_bottom_var.get()),
                }
            )
        else:
            self._clear_crop_settings()
        self._update_crop_status_label()
        self._close_crop_window()

    def _reset_crop_settings(self):
        self.crop_enable_var.set(False)
        for var in (self.crop_left_var, self.crop_right_var, self.crop_top_var, self.crop_bottom_var):
            var.set(0)
        self._draw_crop_rectangle()

    def _clear_crop_settings(self):
        self.crop_settings.update(
            {
                "enabled": False,
                "video": None,
                "left": 0,
                "right": 0,
                "top": 0,
                "bottom": 0,
            }
        )

    def _get_crop_filter_for(self, src: str):
        cfg = self.crop_settings
        if (
            not cfg.get("enabled")
            or cfg.get("video") != src
            or self.target_format.get() == "Original"
        ):
            return None
        left = max(0, min(40, int(cfg.get("left", 0))))
        right = max(0, min(40, int(cfg.get("right", 0))))
        top = max(0, min(40, int(cfg.get("top", 0))))
        bottom = max(0, min(40, int(cfg.get("bottom", 0))))
        if left + right >= 90 or top + bottom >= 90:
            return None
        return (
            f"crop=iw*(1-({left}+{right})/100):"
            f"ih*(1-({top}+{bottom})/100):"
            f"iw*{left}/100:ih*{top}/100"
        )

    # ------------- Localization refresh -------------
    def refresh_language(self):
        """Refresh visible texts according to current language."""
        self.lbl_title.config(text=i18n.t("video.title"))
        self.lf_select.config(text=i18n.t("video.section.select"))
        self.btn_browse.config(text=i18n.t("video.btn.browse_files"))
        self.btn_clear.config(text=i18n.t("video.btn.clear_selected"))
        self.lbl_hint.config(text=i18n.t("video.hint.dragdrop"))
        self.lbl_count.config(text=i18n.t("video.files.count", file_count=len(self.files)))

        self.lf_output.config(text=i18n.t("video.section.output"))
        self.btn_out_browse.config(text=i18n.t("video.output.btn.browse"))
        if not self.output_dir:
            self.lbl_out.config(text=i18n.t("video.output.label.not_selected"))
        self.btn_clear_output.config(text=i18n.t("video.output.btn.clear"))

        self.lf_format.config(text=i18n.t("video.section.format"))
        self.lbl_format.config(text=i18n.t("video.format.label"))
        self.lbl_w.config(text=i18n.t("video.resize.width_short"))
        self.lbl_h.config(text=i18n.t("video.resize.height_short"))
        self.lbl_fps.config(text=i18n.t("video.fps.label"))
        self.btn_gif_settings.config(text=i18n.t("video.gif.btn_settings"))
        self.crop_frame.config(text=i18n.t("video.crop.section"))
        self.btn_crop.config(text=i18n.t("video.crop.btn_open"))
        self._update_crop_button_state()

        self.lf_progress.config(text=i18n.t("video.section.progress"))
        if not self.is_busy and self.lbl_status.cget("text") in ("", i18n.t("video.status.idle")):
            self.lbl_status.config(text=i18n.t("video.status.idle"))
        self.btn_start.config(text=i18n.t("video.btn.start"))

        # If GIF window open, update its labels/buttons
        if hasattr(self, "gif_win") and self.gif_win is not None and tk.Toplevel.winfo_exists(self.gif_win):
            self.gif_win.title(i18n.t("video.gif.window_title"))

    def _is_video(self, path:str)->bool:
        ext=os.path.splitext(path)[1].lower()
        return ext in [".mp4",".mov",".mkv",".avi",".webm",".m4v",".ts"]

    def _avoid_overwrite(self, out_path:str)->str:
        if not os.path.exists(out_path): return out_path
        b,e=os.path.splitext(out_path); i=1
        while True:
            p=f"{b}_{i}{e}"
            if not os.path.exists(p): return p
            i+=1
