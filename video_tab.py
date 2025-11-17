import os, subprocess, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None

VIDEO_FORMATS = ["Original","MP4","MOV","MKV","AVI","WEBM"]

def have_ffmpeg():
    try:
        subprocess.run(["ffmpeg","-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False

class VideoTab:
    def __init__(self, app, parent):
        self.app=app; self.root=app.root; self.parent=parent
        if not have_ffmpeg():
            messagebox.showwarning("FFmpeg not found","FFmpeg is required for Video features.")

        self.files=[]; self.output_dir=""
        self.target_format=tk.StringVar(value="MP4")
        self.keep_aspect=tk.BooleanVar(value=True)
        self.resize_enabled=tk.BooleanVar(value=False)
        self.width=tk.IntVar(value=1920); self.height=tk.IntVar(value=1080)
        self.fps=tk.IntVar(value=0)

        self.is_busy=False
        self.cancel_requested=False
        self.current_proc=None
        self.just_finished=False  # tab change sonrası auto-clear

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        pad={"padx":10,"pady":5}
        main=ttk.Frame(self.parent); main.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(main, text="Bambam Video Converter", font=("Segoe UI",12,"bold")).pack(pady=(0,8))

        files=ttk.LabelFrame(main, text="1) Select Videos"); files.pack(fill="x", **pad)
        ttk.Button(files, text="Browse Videos...", command=self._select_files).pack(side="left", padx=(5,10), pady=5)
        self.lbl_count=ttk.Label(files, text="Selected files: 0"); self.lbl_count.pack(side="left", pady=5)
        self.btn_clear=ttk.Button(files, text="Clear Selected", command=self._clear_selected)
        self.btn_clear.pack(side="right", padx=5)

        out=ttk.LabelFrame(main, text="2) Select Output Folder"); out.pack(fill="x", **pad)
        ttk.Button(out, text="Browse Folder...", command=self._select_output).pack(side="left", padx=5, pady=5)
        self.lbl_out=ttk.Label(out, text="Not selected"); self.lbl_out.configure(foreground="#c7b2ff")
        self.lbl_out.pack(side="left", padx=10)
        ttk.Button(out, text="Clear Output Folder", command=self._clear_output_folder).pack(side="right", padx=5)

        fmt=ttk.LabelFrame(main, text="3) Target Format & Settings"); fmt.pack(fill="x", **pad)
        ttk.Label(fmt, text="Format:").pack(side="left", padx=5, pady=5)
        om=tk.OptionMenu(fmt, self.target_format, *VIDEO_FORMATS, command=self._on_format_change)
        om.pack(side="left", padx=5, pady=5); self._style_optionmenu(om)

        resf=ttk.Frame(fmt); resf.pack(side="left", padx=15, pady=5)
        ttk.Checkbutton(resf, text="Resize", variable=self.resize_enabled,
                        command=self._toggle_resize_controls).pack(side="left")
        ttk.Label(resf, text="W:").pack(side="left", padx=(10,3))
        self.ent_w=tk.Entry(resf, textvariable=self.width, width=6,
                            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"); self.ent_w.pack(side="left")
        ttk.Label(resf, text="H:").pack(side="left", padx=(8,3))
        self.ent_h=tk.Entry(resf, textvariable=self.height, width=6,
                            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"); self.ent_h.pack(side="left")
        ttk.Checkbutton(resf, text="Keep aspect", variable=self.keep_aspect).pack(side="left", padx=(10,0))

        fpsf=ttk.Frame(fmt); fpsf.pack(side="left", padx=15, pady=5)
        ttk.Label(fpsf, text="FPS (0=keep):").pack(side="left", padx=(0,5))
        self.ent_fps=tk.Entry(fpsf, textvariable=self.fps, width=5,
                              bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"); self.ent_fps.pack(side="left")

        prog=ttk.LabelFrame(main, text="Progress"); prog.pack(fill="x", **pad)
        self.progress=ttk.Progressbar(prog, mode="determinate"); self.progress.pack(fill="x", padx=10, pady=6)
        self.lbl_prog=ttk.Label(prog, text="0 / 0"); self.lbl_prog.pack()
        self.lbl_status=ttk.Label(prog, text="Idle."); self.lbl_status.pack(pady=(0,5))

        act=ttk.Frame(main); act.pack(pady=10)
        self.btn_start=ttk.Button(act, text="Start Conversion", command=self._start)
        self.btn_start.pack(side="left", padx=6)
        self.btn_clear_all=ttk.Button(act, text="Clear", command=self._clear_all)
        self.btn_clear_all.pack(side="left", padx=6)

        if DND_FILES:
            try:
                main.drop_target_register(DND_FILES)
                main.dnd_bind("<<Drop>>", self._on_drop)
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

    # ---------------- Selectors ----------------
    def _on_drop(self, event):
        paths=self.root.splitlist(event.data)
        for p in paths:
            p=p.strip()
            if os.path.isdir(p):
                for n in os.listdir(p):
                    fp=os.path.join(p,n)
                    if os.path.isfile(fp) and self._is_video(fp): self.files.append(fp)
            elif os.path.isfile(p) and self._is_video(p): self.files.append(p)
        if self.files:
            self.files=list(dict.fromkeys(self.files))
            self.lbl_count.config(text=f"Selected files: {len(self.files)}")

    def _select_files(self):
        paths=filedialog.askopenfilenames(
            title="Select video files",
            filetypes=[("Video files","*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.ts")]
        )
        if paths:
            self.files=list(dict.fromkeys(self.files + list(paths)))
            self.lbl_count.config(text=f"Selected files: {len(self.files)}")

    def _select_output(self):
        d=filedialog.askdirectory(title="Select output folder")
        if d:
            self.output_dir=d
            self.lbl_out.config(text=d, foreground=self.app.fg)

    # ---------------- Start / Cancel ----------------
    def _start(self):
        if self.is_busy: return
        if not self.files:
            messagebox.showwarning("Warning","Please select at least one video."); return
        if not self.output_dir:
            messagebox.showwarning("Warning","Please select an output folder."); return

        self.is_busy=True
        self.cancel_requested=False
        self.current_proc=None
        self.btn_start.config(state="disabled")
        self.btn_clear.config(state="disabled")
        self.btn_clear_all.config(text="Cancel", command=self._cancel)  # Clear -> Cancel
        self.progress["value"]=0
        self.lbl_prog.config(text=f"0 / {len(self.files)}")
        self.lbl_status.config(text="Processing…")
        threading.Thread(target=self._worker, daemon=True).start()

    def _cancel(self):
        if not self.is_busy: return
        self.cancel_requested=True
        self.lbl_status.config(text="Cancelling…")
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
                    cmd=["ffmpeg","-y","-i",src,"-c","copy",out]
                else:
                    ext=target.lower()
                    out=self._avoid_overwrite(os.path.join(self.output_dir, f"{base}.{ext}"))
                    cmd=["ffmpeg","-y","-i",src]
                    if self.resize_enabled.get():
                        w=self.width.get(); h=self.height.get()
                        if self.keep_aspect.get():
                            cmd+=["-vf", f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"]
                        else:
                            cmd+=["-vf", f"scale={w}:{h}"]
                    if self.fps.get()>0: cmd+=["-r", str(self.fps.get())]
                    vcodec="libx264" if ext in ("mp4","mov","m4v") else ("libvpx-vp9" if ext=="webm" else "libx264")
                    acodec="aac" if ext in ("mp4","mov","m4v") else ("libopus" if ext=="webm" else "aac")
                    cmd+=["-c:v", vcodec, "-c:a", acodec, out]

                # Popen ile başlat -> iptal edilebilir
                self.current_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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

    def _tick(self, done, total):
        self.progress["value"]=(done/total)*100
        self.lbl_prog.config(text=f"{done} / {total}")

    def _finish(self, cancelled):
        self.is_busy=False
        self.btn_start.config(state="normal")
        self.btn_clear.config(state="normal")
        self.btn_clear_all.config(text="Clear", command=self._clear_all)
        if cancelled:
            self.lbl_status.config(text="Cancelled.")
        else:
            self.lbl_status.config(text="Completed.")
            self.just_finished=True  # sonraki girişte temizle

    # ---------------- Helpers / Clear ----------------
    def on_tab_shown(self):
        """Ana notebook tab değişiminde çağrılır."""
        if not self.is_busy and self.just_finished:
            self._clear_all()
            self.just_finished=False

    def _clear_selected(self):
        if self.is_busy: return
        self.files=[]; self.lbl_count.config(text="Selected files: 0")

    def _clear_all(self):
        if self.is_busy:
            # güvenlik: Clear'a basılırsa iptal et
            self._cancel()
            return
        self._clear_selected()
        self.output_dir=""
        self.lbl_out.config(text="Not selected", foreground="#c7b2ff")
        self.progress["value"]=0; self.lbl_prog.config(text="0 / 0"); self.lbl_status.config(text="Idle.")

    def _clear_output_folder(self):
        if not self.output_dir or not os.path.isdir(self.output_dir):
            messagebox.showinfo("Info","Output folder is not set."); return
        if not messagebox.askyesno("Confirm","Delete ALL files in output folder?"): return
        cnt=0
        for n in os.listdir(self.output_dir):
            p=os.path.join(self.output_dir,n)
            if os.path.isfile(p):
                try: os.remove(p); cnt+=1
                except: pass
        messagebox.showinfo("Cleared", f"Deleted {cnt} file(s).")

    def _on_format_change(self, value):
        original=(value=="Original")
        state="disabled" if original else "normal"
        for w in (self.ent_w, self.ent_h, self.ent_fps): w.configure(state=state)
        if original: self.resize_enabled.set(False)
        self._toggle_resize_controls()

    def _toggle_resize_controls(self):
        st="normal" if (self.resize_enabled.get() and self.ent_w.cget("state")=="normal") else "disabled"
        for w in (self.ent_w, self.ent_h): w.configure(state=st)

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
