import os, subprocess, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
import concurrent.futures, multiprocessing

import localization as i18n

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None

VIDEO_FORMATS = ["Original","MP4","MOV","MKV","AVI","WEBM","GIF"]

def get_ffmpeg_cmd():
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, exe)
    if os.path.exists(local):
        return [local]
    return ["ffmpeg"]

def have_ffmpeg():
    try:
        cmd = get_ffmpeg_cmd() + ["-version"]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "FFmpeg error")

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

        # GIF specific settings (use same W/H/FPS by default)
        self.gif_width=tk.IntVar(value=480)
        self.gif_height=tk.IntVar(value=270)
        self.gif_fps=tk.IntVar(value=12)

        self.is_busy=False
        self.cancel_requested=False
        self.current_proc=None
        self.just_finished=False  # tab change sonrası auto-clear

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
        self.btn_browse.pack(side="left", padx=(0,10), pady=2)
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

        self.lf_output=ttk.LabelFrame(main, text=i18n.t("video.section.output")); out=self.lf_output; out.pack(fill="x", **pad)
        self.btn_out_browse = ttk.Button(out, text=i18n.t("video.output.btn.browse"), command=self._select_output)
        self.btn_out_browse.pack(side="left", padx=5, pady=5)
        self.lbl_out=ttk.Label(out, text=i18n.t("video.output.label.not_selected")); self.lbl_out.configure(foreground="#c7b2ff")
        self.lbl_out.pack(side="left", padx=10)
        self.btn_clear_output = ttk.Button(out, text=i18n.t("video.output.btn.clear"), command=self._clear_output_folder)
        self.btn_clear_output.pack(side="right", padx=5)

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

        self.lf_progress=ttk.LabelFrame(main, text=i18n.t("video.section.progress")); prog=self.lf_progress; prog.pack(fill="x", **pad)
        self.progress=ttk.Progressbar(prog, mode="determinate"); self.progress.pack(fill="x", padx=10, pady=6)
        self.lbl_prog=ttk.Label(prog, text=i18n.t("video.progress.initial")); self.lbl_prog.pack()
        self.lbl_status=ttk.Label(prog, text=i18n.t("video.status.idle")); self.lbl_status.pack(pady=(0,5))

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
        for p in paths:
            p=p.strip()
            if os.path.isdir(p):
                for n in os.listdir(p):
                    fp=os.path.join(p,n)
                    if os.path.isfile(fp) and self._is_video(fp): self.files.append(fp)
            elif os.path.isfile(p) and self._is_video(p): self.files.append(p)
        if self.files:
            self.files=list(dict.fromkeys(self.files))
            self.lbl_count.config(text=i18n.t("video.files.count", file_count=len(self.files)))

    def _select_files(self):
        paths=filedialog.askopenfilenames(
            title=i18n.t("video.section.select"),
            filetypes=[(i18n.t("tabs.video"),"*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.ts")]
        )
        if paths:
            self.files=list(dict.fromkeys(self.files + list(paths)))
            self.lbl_count.config(text=i18n.t("video.files.count", file_count=len(self.files)))

    def _select_output(self):
        d=filedialog.askdirectory(title=i18n.t("video.section.output"))
        if d:
            self.output_dir=d
            self.lbl_out.config(text=d, foreground=self.app.fg)

    # ---------------- Start / Cancel ----------------
    def _start(self):
        if self.is_busy: return
        if not self.files:
            messagebox.showwarning(i18n.t("video.warning.title"),i18n.t("video.warning.no_files")); return
        if not self.output_dir:
            messagebox.showwarning(i18n.t("video.warning.title"),i18n.t("video.warning.no_output")); return

        self.is_busy=True
        self.cancel_requested=False
        self.current_proc=None
        self.btn_start.config(state="disabled")
        self.btn_clear.config(state="disabled")
        self.progress["value"]=0
        self.lbl_prog.config(text=f"0 / {len(self.files)}")
        self.lbl_status.config(text=i18n.t("video.status.processing"))
        self.params_list = [
            {
                'src': s,
                'output_dir': self.output_dir,
                'target': self.target_format.get(),
                'resize_enabled': self.resize_enabled.get(),
                'width': self.width.get(),
                'height': self.height.get(),
                'keep_aspect': self.keep_aspect.get(),
                'fps': self.fps.get()
            } for s in self.files
        ]
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
                        if w > 0 and h > 0:
                            filters.append(f"scale={w}:{h}:flags=lanczos")
                        if f > 0:
                            filters.insert(0, f"fps={f}")
                        cmd = get_ffmpeg_cmd() + ["-y","-i", src]
                        if filters:
                            cmd += ["-vf", ",".join(filters)]
                        cmd += ["-loop", "0", out]
                    else:
                        cmd = get_ffmpeg_cmd() + ["-y","-i",src]
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
        self.files=[]; self.lbl_count.config(text=i18n.t("video.files.count", file_count=0))

    def _clear_all(self):
        if self.is_busy:
            # güvenlik: Clear'a basılırsa iptal et
            self._cancel()
            return
        self._clear_selected()
        self.output_dir=""
        self.lbl_out.config(text=i18n.t("video.output.label.not_selected"), foreground="#c7b2ff")
        self.progress["value"]=0; self.lbl_prog.config(text=i18n.t("video.progress.initial")); self.lbl_status.config(text=i18n.t("video.status.idle"))

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
