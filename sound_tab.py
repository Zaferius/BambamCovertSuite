import os, subprocess, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None

AUDIO_FORMATS = ["MP3","WAV","FLAC","OGG","M4A","AAC"]
AUDIO_BITRATES = ["128k","192k","256k","320k"]

def have_ffmpeg():
    try:
        subprocess.run(["ffmpeg","-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False

class SoundTab:
    def __init__(self, app, parent):
        self.app=app; self.root=app.root; self.parent=parent
        if not have_ffmpeg():
            messagebox.showwarning("FFmpeg not found","FFmpeg is required for Sound features.")

        self.audio_files=[]; self.output_dir=""
        self.target_format=tk.StringVar(value="MP3")
        self.bitrate=tk.StringVar(value="192k")
        self.drop_canvas=None
        self.is_busy=False

        self._build_ui(); self._setup_drag_and_drop()

    def _build_ui(self):
        padding={"padx":10,"pady":5}
        main=ttk.Frame(self.parent); main.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(main, text="Bambam Sound Converter", font=("Segoe UI",12,"bold")).pack(pady=(0,8))

        files=ttk.LabelFrame(main, text="1) Select Audio Files"); files.pack(fill="x", **padding)
        self.drop_canvas=tk.Canvas(files, bg=self.app.frame_bg, highlightthickness=0, height=90)
        self.drop_canvas.pack(fill="x", padx=6, pady=6)
        self.drop_canvas.bind("<Configure>", self._draw_drop_zone_border)
        inner=ttk.Frame(self.drop_canvas); self.drop_canvas.create_window(10,10, window=inner, anchor="nw")

        ttk.Button(inner, text="Browse Audio...", command=self.select_files).pack(side="left", padx=(0,10), pady=2)
        self.lbl_file_count=ttk.Label(inner, text="Selected files: 0"); self.lbl_file_count.pack(side="left", pady=2)
        ttk.Label(inner, text="You can also drag & drop audio files onto this area.", wraplength=470, justify="left")\
            .pack(anchor="w", pady=(4,0))

        out=ttk.LabelFrame(main, text="2) Select Output Folder"); out.pack(fill="x", **padding)
        ttk.Button(out, text="Browse Folder...", command=self.select_output_dir).pack(side="left", padx=5, pady=5)
        self.lbl_output_dir=ttk.Label(out, text="Not selected"); self.lbl_output_dir.configure(foreground="#c7b2ff")
        self.lbl_output_dir.pack(side="left", padx=10)
        ttk.Button(out, text="Clear Selected", command=self._clear_selected).pack(side="right", padx=5)
        ttk.Button(out, text="Clear Output Folder", command=self._clear_output_folder).pack(side="right", padx=5)

        fmt=ttk.LabelFrame(main, text="3) Target Format & Bitrate"); fmt.pack(fill="x", **padding)
        ttk.Label(fmt, text="Format:").pack(side="left", padx=5, pady=5)
        self.format_menu=tk.OptionMenu(fmt, self.target_format, *AUDIO_FORMATS); self.format_menu.pack(side="left", padx=5, pady=5)
        self._style_optionmenu(self.format_menu)

        bf=ttk.Frame(fmt); bf.pack(side="left", padx=15, pady=5)
        ttk.Label(bf, text="Bitrate:").pack(side="left", padx=(0,5))
        self.bitrate_menu=tk.OptionMenu(bf, self.bitrate, *AUDIO_BITRATES); self.bitrate_menu.pack(side="left")
        self._style_optionmenu(self.bitrate_menu)

        prog=ttk.LabelFrame(main, text="Progress"); prog.pack(fill="x", **padding)
        self.progress=ttk.Progressbar(prog, mode="determinate"); self.progress.pack(fill="x", padx=10, pady=5)
        self.lbl_progress=ttk.Label(prog, text="0 / 0"); self.lbl_progress.pack()
        self.lbl_status=ttk.Label(prog, text="Idle."); self.lbl_status.pack(pady=(0,5))

        act=ttk.Frame(main); act.pack(pady=10)
        self.btn_convert=ttk.Button(act, text="Start Conversion", command=self.start_conversion)
        self.btn_convert.pack(side="left", padx=6)
        ttk.Button(act, text="Clear", command=self._clear_all).pack(side="left", padx=6)

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
        self.lbl_file_count.config(text=f"Selected files: {len(self.audio_files)}")

    def select_files(self):
        ft=[("Audio files","*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma")]
        paths=filedialog.askopenfilenames(title="Select audio files", filetypes=ft)
        if paths:
            self.audio_files=list(dict.fromkeys(self.audio_files + list(paths)))
            self.update_file_count()

    def select_output_dir(self):
        d=filedialog.askdirectory(title="Select output folder")
        if d:
            self.output_dir=d
            short=d if len(d)<=45 else "..."+d[-45:]
            self.lbl_output_dir.config(text=short, foreground=self.app.fg)

    def start_conversion(self):
        if self.is_busy: return
        if not self.audio_files:
            messagebox.showwarning("Warning","Please select at least one audio file."); return
        if not self.output_dir:
            messagebox.showwarning("Warning","Please select an output folder."); return
        self.is_busy=True
        self.btn_convert.config(state="disabled")
        self.progress["value"]=0
        self.lbl_progress.config(text=f"0 / {len(self.audio_files)}")
        self.lbl_status.config(text="Processing…")
        threading.Thread(target=self.convert_audio, daemon=True).start()

    def convert_audio(self):
        total=len(self.audio_files); done=0; errors=[]
        target=self.target_format.get().upper(); fmt=target.lower(); bitrate=self.bitrate.get()
        for path in self.audio_files:
            try:
                base=os.path.splitext(os.path.basename(path))[0].replace(os.sep,"_")
                out=self._avoid_overwrite(os.path.join(self.output_dir, f"{base}.{fmt}"))
                cmd=["ffmpeg","-y","-i",path]
                if fmt in ["mp3","ogg","m4a","aac"]: cmd+=["-b:a", bitrate]
                cmd+=[out]
                res=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode!=0: raise RuntimeError(res.stderr.strip() or "ffmpeg error")
            except Exception as e:
                errors.append((path,str(e)))
            finally:
                done+=1
                self.root.after(0, self._tick_progress, done, total)
        self.root.after(0, self._finish, total, errors)

    def _tick_progress(self, done, total):
        self.progress["value"]=(done/total)*100
        self.lbl_progress.config(text=f"{done} / {total}")

    def _finish(self, total, errors):
        self.is_busy=False
        self.btn_convert.config(state="normal")
        if errors:
            self.lbl_status.config(text="Completed with errors.")
            msg=("Audio conversion finished with errors.\n\n"
                 f"{len(errors)} of {total} file(s) failed.\n\n"
                 f"First error:\n{errors[0][0]}\n{errors[0][1]}")
            messagebox.showwarning("Completed with errors", msg)
        else:
            self.lbl_status.config(text="Completed.")
            messagebox.showinfo("Done", "All audio conversions finished.")

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
            messagebox.showinfo("Info","Output folder is not set."); return
        if not messagebox.askyesno("Confirm","Delete ALL files in output folder?"): return
        cnt=0
        for n in os.listdir(self.output_dir):
            p=os.path.join(self.output_dir,n)
            if os.path.isfile(p):
                try: os.remove(p); cnt+=1
                except: pass
        messagebox.showinfo("Cleared", f"Deleted {cnt} file(s).")
    def _clear_all(self):
        self._clear_selected()
        self.output_dir=""; self.lbl_output_dir.config(text="Not selected", foreground="#c7b2ff")
        self.progress["value"]=0; self.lbl_progress.config(text="0 / 0"); self.lbl_status.config(text="Idle.")
