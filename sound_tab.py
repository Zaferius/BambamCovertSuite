import os, subprocess, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
import concurrent.futures, multiprocessing

import localization as i18n

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None

AUDIO_FORMATS = ["MP3","WAV","FLAC","OGG","M4A","AAC"]
AUDIO_BITRATES = ["128k","192k","256k","320k"]

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

class SoundTab:
    def __init__(self, app, parent):
        self.app=app; self.root=app.root; self.parent=parent
        if not have_ffmpeg():
            messagebox.showwarning(i18n.t("sound.ffmpeg.missing_title"), i18n.t("sound.ffmpeg.missing_message"))

        self.audio_files=[]; self.output_dir=""
        self.target_format=tk.StringVar(value="MP3")
        self.bitrate=tk.StringVar(value="192k")
        self.drop_canvas=None
        self.is_busy=False
        
        # Output location settings
        self.mirror_to_source = tk.BooleanVar(value=False)
        self.delete_originals = tk.BooleanVar(value=False)
        self.radio_var = None

        self._build_ui(); self._setup_drag_and_drop()

    def _build_ui(self):
        padding={"padx":10,"pady":5}
        main=ttk.Frame(self.parent); main.pack(fill="both", expand=True, padx=8, pady=8)
        self.lbl_title = ttk.Label(main, text=i18n.t("sound.title"), font=("Segoe UI",12,"bold"))
        self.lbl_title.pack(pady=(0,8))

        self.lf_select = ttk.LabelFrame(main, text=i18n.t("sound.section.select")); files=self.lf_select; files.pack(fill="x", **padding)
        self.drop_canvas=tk.Canvas(files, bg=self.app.frame_bg, highlightthickness=0, height=120)
        self.drop_canvas.pack(fill="x", padx=6, pady=6)
        self.drop_canvas.bind("<Configure>", self._draw_drop_zone_border)
        inner=ttk.Frame(self.drop_canvas); self.drop_canvas.create_window(10,10, window=inner, anchor="nw")

        top=ttk.Frame(inner); top.pack(fill="x")

        self.btn_browse = ttk.Button(top, text=i18n.t("sound.btn.browse_files"), command=self.select_files)
        self.btn_browse.pack(side="left", padx=(0,8), pady=2)
        self.btn_add_folders = ttk.Button(top, text=i18n.t("sound.btn.add_folders"), command=self.add_folders)
        self.btn_add_folders.pack(side="left", padx=(0,8), pady=2)

        self.lbl_file_count=ttk.Label(top, text=i18n.t("sound.files.count", file_count=0))
        self.lbl_file_count.pack(side="left", pady=2)
        self.btn_clear = ttk.Button(top, text=i18n.t("sound.btn.clear_selected"), command=self._clear_selected)
        self.btn_clear.pack(side="right", padx=5)

        self.lbl_hint=ttk.Label(
            inner,
            text=i18n.t("sound.hint.dragdrop"),
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

        self.lf_output=ttk.LabelFrame(main, text=i18n.t("sound.section.output")); out=self.lf_output; out.pack(fill="x", **padding)
        
        self.radio_var = tk.StringVar(value="mirror" if self.mirror_to_source.get() else "folder")
        
        # radio: use folder (üstte, browse button yanında)
        row1 = ttk.Frame(out); row1.pack(fill="x", padx=6, pady=(6, 2))
        self.rb_folder = ttk.Radiobutton(row1, text=i18n.t("image.output.radio.folder"),
                                         value="folder", variable=self.radio_var,
                                         command=self._on_output_mode_change)
        self.rb_folder.pack(side="left")
        self.rb_folder.configure(style="White.TRadiobutton")
        self.btn_out_browse = ttk.Button(row1, text=i18n.t("sound.output.btn.browse"), command=self.select_output_dir)
        self.btn_out_browse.pack(side="left", padx=(12, 8))
        self.lbl_output_dir = ttk.Label(row1, text=i18n.t("sound.output.label.not_selected"))
        self.lbl_output_dir.configure(foreground="#c7b2ff")
        self.lbl_output_dir.pack(side="left", padx=(6, 0))
        self.btn_clear_output = ttk.Button(row1, text=i18n.t("sound.output.btn.clear"), command=self._clear_output_folder)
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

        self.lf_format=ttk.LabelFrame(main, text=i18n.t("sound.section.format")); fmt=self.lf_format; fmt.pack(fill="x", **padding)
        self.lbl_format = ttk.Label(fmt, text=i18n.t("sound.format.label")); self.lbl_format.pack(side="left", padx=5, pady=5)
        self.format_menu=tk.OptionMenu(fmt, self.target_format, *AUDIO_FORMATS); self.format_menu.pack(side="left", padx=5, pady=5)
        self._style_optionmenu(self.format_menu)

        bf=ttk.Frame(fmt); bf.pack(side="left", padx=15, pady=5)
        self.lbl_bitrate = ttk.Label(bf, text=i18n.t("sound.bitrate.label")); self.lbl_bitrate.pack(side="left", padx=(0,5))
        self.bitrate_menu=tk.OptionMenu(bf, self.bitrate, *AUDIO_BITRATES); self.bitrate_menu.pack(side="left")
        self._style_optionmenu(self.bitrate_menu)

        self.lf_progress=ttk.LabelFrame(main, text=i18n.t("sound.section.progress")); prog=self.lf_progress; prog.pack(fill="x", **padding)
        
        # Individual file progress (yellow bar)
        file_prog_frame = ttk.Frame(prog)
        file_prog_frame.pack(fill="x", padx=10, pady=(4, 1))
        self.lbl_file_prog = ttk.Label(file_prog_frame, text="", font=("", 8))
        self.lbl_file_prog.pack(anchor="w", pady=(0, 1))
        try:
            style = ttk.Style()
            style.configure("Yellow.Horizontal.TProgressbar", background="#ffd700", troughcolor="#2b2b2b", thickness=20)
            self.file_progress = ttk.Progressbar(file_prog_frame, mode="determinate", style="Yellow.Horizontal.TProgressbar")
        except Exception:
            self.file_progress = ttk.Progressbar(file_prog_frame, mode="determinate")
        self.file_progress.pack(fill="x", ipady=8)
        
        # Overall progress (main bar)
        overall_prog_frame = ttk.Frame(prog)
        overall_prog_frame.pack(fill="x", padx=10, pady=(3, 4))
        self.lbl_progress=ttk.Label(overall_prog_frame, text=i18n.t("sound.progress.initial"), font=("", 8))
        self.lbl_progress.pack(anchor="w", pady=(0, 1))
        self.progress=ttk.Progressbar(overall_prog_frame, mode="determinate")
        self.progress.pack(fill="x", ipady=8)
        
        self.lbl_status=ttk.Label(prog, text=i18n.t("sound.status.idle"))
        self.lbl_status.pack(pady=(2,4))

        act=ttk.Frame(main); act.pack(pady=10)
        self.btn_convert=ttk.Button(act, text=i18n.t("sound.btn.start"), command=self.start_conversion)
        self.btn_convert.pack(side="left", padx=6)

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

    def _setup_drag_and_drop(self):
        if DND_FILES:
            try:
                self.drop_canvas.drop_target_register(DND_FILES)
                self.drop_canvas.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                pass

    def on_drop(self, event):
        paths=self.root.splitlist(event.data); new=[]
        for p in paths:
            p=p.strip()
            if os.path.isdir(p):
                for n in os.listdir(p):
                    fp=os.path.join(p,n)
                    if os.path.isfile(fp) and self.is_audio_file(fp): new.append(fp)
            elif os.path.isfile(p) and self.is_audio_file(p): new.append(p)
        if new:
            self.audio_files=list(dict.fromkeys(self.audio_files + new))
            self.update_file_count()

    def is_audio_file(self, path:str)->bool:
        ext=os.path.splitext(path)[1].lower()
        return ext in [".mp3",".wav",".flac",".ogg",".m4a",".aac",".wma"]

    def update_file_count(self):
        self.lbl_file_count.config(text=i18n.t("sound.files.count", file_count=len(self.audio_files)))

    def select_files(self):
        ft=[(i18n.t("tabs.sound"),"*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma")]
        paths=filedialog.askopenfilenames(title=i18n.t("sound.section.select"), filetypes=ft)
        if paths:
            self.audio_files=list(dict.fromkeys(self.audio_files + list(paths)))
            self.update_file_count()

    def add_folders(self):
        folders = []
        while True:
            d = filedialog.askdirectory(title=i18n.t("sound.section.select"))
            if not d:
                break
            folders.append(d)
            if not messagebox.askyesno(i18n.t("sound.clear_output.confirm_title"), "Add another folder?"):
                break
        if not folders:
            return
        new = []
        for folder in folders:
            for rootdir, _, files in os.walk(folder):
                for name in files:
                    fp = os.path.join(rootdir, name)
                    if os.path.isfile(fp) and self.is_audio_file(fp):
                        new.append(fp)
        if new:
            self.audio_files = list(dict.fromkeys(self.audio_files + new))
            self.update_file_count()

    def select_output_dir(self):
        d=filedialog.askdirectory(title=i18n.t("sound.section.output"))
        if d:
            self.output_dir=d
            short=d if len(d)<=45 else "..."+d[-45:]
            self.lbl_output_dir.config(text=short, foreground=self.app.fg)
    
    def _on_output_mode_change(self):
        use_mirror = (self.radio_var.get() == "mirror")
        self.mirror_to_source.set(use_mirror)
        state = "disabled" if use_mirror else "normal"
        self.btn_out_browse.configure(state=state)
        self.btn_clear_output.configure(state=state)
        
        if use_mirror:
            self.lbl_output_dir.pack_forget()
        else:
            if not self.lbl_output_dir.winfo_ismapped():
                self.lbl_output_dir.pack(side="left", padx=(6, 0))
            if self.output_dir:
                text = self.output_dir if len(self.output_dir) <= 45 else "..." + self.output_dir[-45:]
                self.lbl_output_dir.configure(text=text, foreground=self.app.fg)
            else:
                self.lbl_output_dir.configure(text=i18n.t("sound.output.label.not_selected"), foreground="#c7b2ff")

    def start_conversion(self):
        if self.is_busy: return
        if not self.audio_files:
            messagebox.showwarning(i18n.t("sound.warning.title"), i18n.t("sound.warning.no_files")); return
        if not self.mirror_to_source.get() and not self.output_dir:
            messagebox.showwarning(i18n.t("sound.warning.title"), i18n.t("sound.warning.no_output")); return
        self.is_busy=True
        self.btn_convert.config(state="disabled")
        self.progress["value"]=0
        self.file_progress["value"]=0
        self.lbl_progress.config(text=f"Overall: 0 / {len(self.audio_files)}")
        self.lbl_file_prog.config(text="")
        self.lbl_status.config(text=i18n.t("sound.status.processing"))
        threading.Thread(target=self.convert_audio, daemon=True).start()

    def convert_audio(self):
        total=len(self.audio_files); done=0; errors=[]
        target=self.target_format.get().upper(); fmt=target.lower(); bitrate=self.bitrate.get()
        delete_orig = self.delete_originals.get()
        
        for path in self.audio_files:
            filename = os.path.basename(path)
            self.root.after(0, lambda f=filename: self.lbl_file_prog.config(text=f"Processing: {f}"))
            self.root.after(0, lambda: self.file_progress.config(value=0))
            
            try:
                # Determine output directory
                if self.mirror_to_source.get():
                    out_dir = os.path.dirname(path)
                else:
                    out_dir = self.output_dir
                
                base=os.path.splitext(os.path.basename(path))[0].replace(os.sep,"_")
                out=self._avoid_overwrite(os.path.join(out_dir, f"{base}.{fmt}"))
                cmd = get_ffmpeg_cmd() + ["-y","-i",path]
                if fmt in ["mp3","ogg","m4a","aac"]: cmd+=["-b:a", bitrate]
                cmd+=[out]
                res=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode!=0: raise RuntimeError(res.stderr.strip() or "ffmpeg error")
                
                # Delete original if requested and conversion was successful
                if delete_orig and os.path.exists(out):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            except Exception as e:
                errors.append((path,str(e)))
            finally:
                done+=1
                self.root.after(0, lambda: self.file_progress.config(value=100))
                self.root.after(0, self._tick_progress, done, total)
        self.root.after(0, self._finish, total, errors)

    def _tick_progress(self, done, total):
        self.progress["value"]=(done/total)*100
        self.lbl_progress.config(text=f"Overall: {done} / {total}")

    def _finish(self, total, errors):
        self.is_busy=False
        self.btn_convert.config(state="normal")
        if errors:
            self.lbl_status.config(text=i18n.t("sound.result.errors_status"))
            first = errors[0]
            msg = i18n.t(
                "sound.result.errors_message",
                failed=len(errors),
                total=total,
                path=first[0],
                error=first[1],
            )
            messagebox.showwarning(i18n.t("sound.result.errors_title"), msg)
        else:
            self.lbl_status.config(text=i18n.t("sound.result.done_status"))
            messagebox.showinfo(i18n.t("sound.result.done_title"), i18n.t("sound.result.done_message"))
            self.app.open_folder_if_enabled(self.output_dir)

    def _avoid_overwrite(self, out_path:str)->str:
        if not os.path.exists(out_path): return out_path
        b,e=os.path.splitext(out_path); i=1
        while True:
            p=f"{b}_{i}{e}"
            if not os.path.exists(p): return p
            i+=1

    # clears
    def _clear_selected(self):
        self.audio_files=[]; self.update_file_count()
    def _clear_output_folder(self):
        if not self.output_dir or not os.path.isdir(self.output_dir):
            messagebox.showinfo(i18n.t("sound.info.title"),i18n.t("sound.info.output_not_set")); return
        if not messagebox.askyesno(i18n.t("sound.clear_output.confirm_title"),i18n.t("sound.clear_output.confirm_message")): return
        cnt=0
        for n in os.listdir(self.output_dir):
            p=os.path.join(self.output_dir,n)
            if os.path.isfile(p):
                try: os.remove(p); cnt+=1
                except: pass
        messagebox.showinfo(i18n.t("sound.clear_output.done_title"), i18n.t("sound.clear_output.done_message", count=cnt))
    def _clear_all(self):
        self._clear_selected()
        self.output_dir=""; self.lbl_output_dir.config(text=i18n.t("sound.output.label.not_selected"), foreground="#c7b2ff")
        self.progress["value"]=0; self.lbl_progress.config(text=i18n.t("sound.progress.initial")); self.lbl_status.config(text=i18n.t("sound.status.idle"))

    # ------------- Localization refresh -------------
    def refresh_language(self):
        """Refresh visible texts according to current language."""
        self.lbl_title.config(text=i18n.t("sound.title"))
        self.lf_select.config(text=i18n.t("sound.section.select"))
        self.btn_browse.config(text=i18n.t("sound.btn.browse_files"))
        self.btn_add_folders.config(text=i18n.t("sound.btn.add_folders"))
        self.btn_clear.config(text=i18n.t("sound.btn.clear_selected"))
        self.lbl_hint.config(text=i18n.t("sound.hint.dragdrop"))

        self.lf_output.config(text=i18n.t("sound.section.output"))
        self.btn_out_browse.config(text=i18n.t("sound.output.btn.browse"))
        if not self.output_dir:
            self.lbl_output_dir.config(text=i18n.t("sound.output.label.not_selected"))
        self.btn_clear_output.config(text=i18n.t("sound.output.btn.clear"))

        self.lf_format.config(text=i18n.t("sound.section.format"))
        self.lbl_format.config(text=i18n.t("sound.format.label"))
        self.lbl_bitrate.config(text=i18n.t("sound.bitrate.label"))

        self.lf_progress.config(text=i18n.t("sound.section.progress"))
        # Status/progress text kalıcı duruma göre değişir, sadece boşsa idle yapıyoruz
        if not self.is_busy and (self.lbl_status.cget("text") in ("", i18n.t("sound.status.idle"))):
            self.lbl_status.config(text=i18n.t("sound.status.idle"))
        self.btn_convert.config(text=i18n.t("sound.btn.start"))

        # count label'i güncelle
        self.update_file_count()
