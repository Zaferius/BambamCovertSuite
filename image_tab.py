import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None

IMAGE_FORMAT_MAP = {
    "Original": (None, None),            # yeni: format değiştirmeden kopyala
    "PNG": ("PNG", "png"),
    "JPG": ("JPEG", "jpg"),
    "JPEG": ("JPEG", "jpg"),
    "WEBP": ("WEBP", "webp"),
    "TIFF": ("TIFF", "tiff"),
    "BMP": ("BMP", "bmp"),
    "GIF": ("GIF", "gif"),
}

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".tiff", ".tif", ".gif"}


class ImageTab:
    def __init__(self, app, parent):
        self.app = app
        self.root = app.root
        self.parent = parent

        # state
        self.file_paths = []          # tekil dosyalar
        self.folder_paths = []        # eklenen klasörler (recursive)
        self.output_dir = ""
        self.target_format = tk.StringVar(value="PNG")
        self.quality_var = tk.IntVar(value=90)

        self.rename_enabled = tk.BooleanVar(value=False)
        self.rename_pattern = tk.StringVar(value="{name}_converted_{index}")

        # yeni: mirror & delete
        self.mirror_to_source = tk.BooleanVar(value=False)
        self.delete_originals = tk.BooleanVar(value=False)

        self.drop_canvas = None
        self.lbl_hint = None
        self.is_busy = False

        self._build_ui()
        self._setup_drag_and_drop()

    # ---------------- UI ----------------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}
        main = ttk.Frame(self.parent)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(main, text="Bambam Image Converter",
                  font=("Segoe UI", 12, "bold")).pack(pady=(0, 8))

        # 1) Select images (drop zone)
        files = ttk.LabelFrame(main, text="1) Select Images / Folders")
        files.pack(fill="x", **pad)

        self.drop_canvas = tk.Canvas(files, bg=self.app.frame_bg,
                                     highlightthickness=0, height=120)
        self.drop_canvas.pack(fill="x", padx=6, pady=6)
        self.drop_canvas.bind("<Configure>", self._on_drop_canvas_resize)

        inner = ttk.Frame(self.drop_canvas)
        self.drop_canvas.create_window(10, 10, window=inner, anchor="nw")

        top = ttk.Frame(inner)
        top.pack(fill="x")

        ttk.Button(top, text="Browse Images...", command=self.select_files)\
            .pack(side="left", padx=(0, 8), pady=2)

        ttk.Button(top, text="Add Folder...", command=self.add_folder)\
            .pack(side="left", padx=(0, 8), pady=2)

        self.lbl_file_count = ttk.Label(top, text="Selected files: 0 | Selected folders: 0")
        self.lbl_file_count.pack(side="left", pady=2)

        self.lbl_hint = ttk.Label(
            inner,
            text="You can also drag & drop files or folders onto this area (recursive).",
            wraplength=460,
            justify="left",
        )
        self.lbl_hint.pack(fill="x", anchor="w", pady=(6, 4))

        # 2) Output location
        out = ttk.LabelFrame(main, text="2) Output Location")
        out.pack(fill="x", **pad)

        self.radio_var = tk.StringVar(value="mirror" if self.mirror_to_source.get() else "folder")

        # radio: use folder
        row1 = ttk.Frame(out); row1.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Radiobutton(row1, text="Use selected output folder",
                        value="folder", variable=self.radio_var,
                        command=self._on_output_mode_change).pack(side="left")
        ttk.Button(row1, text="Browse Folder...", command=self.select_output_dir)\
            .pack(side="left", padx=(12, 8))
        self.lbl_output_dir = ttk.Label(row1, text="Not selected")
        self.lbl_output_dir.configure(foreground="#c7b2ff")
        self.lbl_output_dir.pack(side="left", padx=(6, 0))

        # radio: mirror to source
        row2 = ttk.Frame(out); row2.pack(fill="x", padx=6, pady=(2, 6))
        ttk.Radiobutton(row2, text="Same folder as source (mirror)",
                        value="mirror", variable=self.radio_var,
                        command=self._on_output_mode_change).pack(side="left")

        # delete originals
        ttk.Checkbutton(out, text="Delete originals after successful conversion",
                        variable=self.delete_originals).pack(anchor="w", padx=6, pady=(0, 6))

        # 3) Target format + quality
        fmt = ttk.LabelFrame(main, text="3) Target Format")
        fmt.pack(fill="x", **pad)
        ttk.Label(fmt, text="Format:").pack(side="left", padx=5, pady=5)

        options = list(IMAGE_FORMAT_MAP.keys())
        self.format_menu = tk.OptionMenu(fmt, self.target_format, *options, command=self.on_format_selected)
        self.format_menu.pack(side="left", padx=5, pady=5)
        self._style_optionmenu(self.format_menu)

        self.frame_quality = ttk.Frame(fmt)
        self.frame_quality.pack(side="left", padx=15, pady=5)
        ttk.Label(self.frame_quality, text="JPEG Quality:").pack(side="left", padx=(0, 5))
        self.lbl_quality_value = ttk.Label(self.frame_quality, text=f"{self.quality_var.get()}")
        self.lbl_quality_value.pack(side="right", padx=(5, 0))
        self.quality_scale = ttk.Scale(
            self.frame_quality, from_=40, to=100, orient="horizontal",
            variable=self.quality_var, command=lambda v: self.update_quality_label(),
            length=150
        )
        self.quality_scale.pack(side="right")

        # 4) Batch rename
        rename = ttk.LabelFrame(main, text="4) Batch Rename (optional)")
        rename.pack(fill="x", **pad)
        ttk.Checkbutton(rename, text="Enable batch renaming",
                        variable=self.rename_enabled, command=self.on_rename_toggle)\
            .pack(anchor="w", padx=5, pady=3)
        self.rename_content = ttk.Frame(rename)
        row = ttk.Frame(self.rename_content); row.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Label(row, text="Pattern:").pack(side="left", padx=(0, 5))
        self.entry_pattern = tk.Entry(
            row, textvariable=self.rename_pattern,
            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"
        )
        self.entry_pattern.pack(side="left", fill="x", expand=True)
        ttk.Label(self.rename_content,
                  text="Placeholders: {name} = original name, {index} = 1,2,3...")\
            .pack(anchor="w", padx=5, pady=(0, 3))
        self.on_rename_toggle()

        # 5) Progress
        prog = ttk.LabelFrame(main, text="Progress")
        prog.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(prog, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)
        self.lbl_progress = ttk.Label(prog, text="0 / 0"); self.lbl_progress.pack(pady=(0, 2))
        self.lbl_status = ttk.Label(prog, text="Idle."); self.lbl_status.pack(pady=(0, 5))

        # 6) Actions
        actions = ttk.Frame(main); actions.pack(pady=10)
        self.btn_convert = ttk.Button(actions, text="Start Conversion", command=self.start_conversion)
        self.btn_convert.pack(side="left", padx=6)
        ttk.Button(actions, text="Clear Selected", command=self._clear_selected).pack(side="left", padx=6)
        ttk.Button(actions, text="Clear Output Folder", command=self._clear_output_folder).pack(side="left", padx=6)

        # initial visibility
        self.on_format_selected(self.target_format.get())
        self._on_output_mode_change()

    def _style_optionmenu(self, om):
        om.config(bg=self.app.entry_bg, fg=self.app.fg,
                  activebackground=self.app.button_hover, activeforeground=self.app.fg,
                  highlightthickness=1, highlightbackground=self.app.border,
                  relief="flat", font=self.app.title_font)
        om["menu"].config(bg=self.app.entry_bg, fg=self.app.fg,
                          activebackground=self.app.button_hover, activeforeground=self.app.fg,
                          font=self.app.title_font)

    # ------------- Drop zone draw / wrap -------------
    def _on_drop_canvas_resize(self, event):
        self._draw_drop_zone_border(event)
        if self.lbl_hint is not None:
            self.lbl_hint.config(wraplength=max(260, event.width - 40))

    def _draw_drop_zone_border(self, event):
        self.drop_canvas.delete("border")
        m = 4
        self.drop_canvas.create_rectangle(m, m, event.width - m, event.height - m,
                                          outline=self.app.fg, dash=(4, 3),
                                          width=1, tags="border")

    # ------------- Drag & Drop -------------
    def _setup_drag_and_drop(self):
        if DND_FILES:
            try:
                self.drop_canvas.drop_target_register(DND_FILES)
                self.drop_canvas.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                pass

    def on_drop(self, event):
        paths = self.root.splitlist(event.data)
        any_added = False
        for p in paths:
            p = p.strip()
            if os.path.isdir(p):
                self.folder_paths.append(p)
                any_added = True
            elif os.path.isfile(p) and self._is_image_file(p):
                self.file_paths.append(p)
                any_added = True
        if any_added:
            self._dedupe_inputs()
            self._update_counts()

    # ------------- File Pickers -------------
    def select_files(self):
        ft = [("All Images", "*.png *.jpg *.jpeg *.jfif *.webp *.bmp *.tiff *.tif *.gif")]
        paths = filedialog.askopenfilenames(title="Select images", filetypes=ft)
        if paths:
            self.file_paths.extend(list(paths))
            self._dedupe_inputs()
            self._update_counts()

    def add_folder(self):
        d = filedialog.askdirectory(title="Select folder")
        if d:
            self.folder_paths.append(d)
            self._dedupe_inputs()
            self._update_counts()

    def select_output_dir(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.output_dir = d
            short = d if len(d) <= 45 else "..." + d[-45:]
            self.lbl_output_dir.config(text=short, foreground=self.app.fg)

    def _on_output_mode_change(self):
        use_mirror = (self.radio_var.get() == "mirror")
        self.mirror_to_source.set(use_mirror)
        # output dir satırını enable/disable et
        state = "disabled" if use_mirror else "normal"
        # labelframe içindeki Browse ve label'ı bul
        # (ilk satırda oldukları için pack_slaves ile erişiyoruz)
        # sadece görsel disable etkisi için butonu disable ediyoruz
        for child in self.lbl_output_dir.master.pack_slaves():
            if isinstance(child, ttk.Button):
                child.configure(state=state)
        self.lbl_output_dir.configure(text=("Using source folders" if use_mirror else
                                            (self.output_dir if self.output_dir else "Not selected")),
                                      foreground=self.app.fg if not use_mirror else "#c7ffcf")
        # "Original" + delete originals kombinasyonunda guard
        self._update_delete_guard()

    # ------------- Helpers -------------
    def _dedupe_inputs(self):
        self.file_paths = list(dict.fromkeys(self.file_paths))
        self.folder_paths = list(dict.fromkeys(self.folder_paths))

    def _update_counts(self):
        self.lbl_file_count.config(
            text=f"Selected files: {len(self.file_paths)} | Selected folders: {len(self.folder_paths)}"
        )

    def _is_image_file(self, path: str) -> bool:
        return os.path.splitext(path)[1].lower() in SUPPORTED_EXTS

    def update_quality_label(self):
        self.lbl_quality_value.config(text=str(int(self.quality_var.get())))

    def on_format_selected(self, value):
        value = value.upper()
        if value in ("JPG", "JPEG"):
            self.frame_quality.pack(side="left", padx=15, pady=5)
        else:
            self.frame_quality.pack_forget()
        self._update_delete_guard()

    def _update_delete_guard(self):
        # "Original" seçiliyken delete originals kilitli (mantıksız riskli)
        if self.target_format.get().upper() == "ORIGINAL":
            self.delete_originals.set(False)
            # disable checkbutton (bulup kapat)
            for ch in self.parent.pack_slaves():
                pass  # noop (stil karmaşık; bırakılan state yeterli)
        # checkbuttonu özel aramadan bırakıyoruz; kullanıcı yine aktif görebilir ama set False kalıyor

    def on_rename_toggle(self):
        if self.rename_enabled.get():
            self.rename_content.pack(fill="x", padx=0, pady=(0, 5))
        else:
            self.rename_content.pack_forget()

    # ------------- Conversion -------------
    def start_conversion(self):
        if self.is_busy:
            return
        if not self.file_paths and not self.folder_paths:
            messagebox.showwarning("Warning", "Please select at least one image or folder.")
            return
        if not self.mirror_to_source.get() and not self.output_dir:
            messagebox.showwarning("Warning", "Please select an output folder or choose 'Same folder as source'.")
            return

        # kaynak listesini hazırlayalım (recursive)
        jobs = []
        for f in self.file_paths:
            if os.path.isfile(f) and self._is_image_file(f):
                jobs.append(f)
        for folder in self.folder_paths:
            for rootdir, _, files in os.walk(folder):
                for name in files:
                    p = os.path.join(rootdir, name)
                    if self._is_image_file(p):
                        jobs.append(p)

        if not jobs:
            messagebox.showinfo("Info", "No images found.")
            return

        self.is_busy = True
        self.btn_convert.config(state="disabled")
        self.progress["value"] = 0
        self.lbl_progress.config(text=f"0 / {len(jobs)}")
        self.lbl_status.config(text="Processing…")

        threading.Thread(target=self._convert_worker, args=(jobs,), daemon=True).start()

    def _convert_worker(self, jobs):
        total = len(jobs)
        errors = []

        fmt_key = self.target_format.get().upper()
        pil_format, ext = IMAGE_FORMAT_MAP.get(fmt_key, ("PNG", "png"))

        idx = 0
        for i, src_path in enumerate(jobs, start=1):
            try:
                src_dir = os.path.dirname(src_path)
                # çıkış klasörü
                out_dir = src_dir if self.mirror_to_source.get() else self.output_dir

                with Image.open(src_path) as img:
                    if pil_format is None:
                        # Original: sadece kopyala (Pillow üzerinden yeniden kaydet)
                        orig_ext = os.path.splitext(src_path)[1].lstrip(".")
                        base_name = self._build_base_name(src_path, i)
                        out_path = self._avoid_overwrite(os.path.join(out_dir, f"{base_name}.{orig_ext}"))
                        img.save(out_path)
                        # original delete — Original modda güvenlik için devre dışı (guard üstte)
                    else:
                        if pil_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                            img = img.convert("RGB")

                        base_name = self._build_base_name(src_path, i)
                        out_path = self._avoid_overwrite(os.path.join(out_dir, f"{base_name}.{ext}"))

                        kwargs = {}
                        if pil_format == "JPEG":
                            q = int(self.quality_var.get())
                            kwargs = dict(quality=q, optimize=True, progressive=True)
                        elif pil_format == "WEBP":
                            q = int(self.quality_var.get())
                            kwargs = dict(quality=q, method=6)

                        img.save(out_path, pil_format, **kwargs)

                        # başarılıysa, istenirse orijinali sil
                        if self.delete_originals.get():
                            try:
                                os.remove(src_path)
                            except Exception:
                                # silinemezse görmezden gel, hata listesine ekleme
                                pass

            except Exception as e:
                errors.append((src_path, str(e)))

            idx = i
            self.root.after(0, self._tick_progress, idx, total)

        self.root.after(0, self._finish_progress, total, errors)

    def _build_base_name(self, src_path: str, idx: int) -> str:
        orig_name = os.path.splitext(os.path.basename(src_path))[0]
        if self.rename_enabled.get():
            try:
                base = self.rename_pattern.get().format(name=orig_name, index=idx)
            except Exception:
                base = f"{orig_name}_{idx}"
        else:
            base = orig_name
        return base.replace(os.sep, "_")

    def _avoid_overwrite(self, out_path: str) -> str:
        if not os.path.exists(out_path):
            return out_path
        base, ext = os.path.splitext(out_path)
        counter = 1
        while True:
            candidate = f"{base}_{counter}{ext}"
            if not os.path.exists(candidate):
                return candidate
            counter += 1

    def _tick_progress(self, current, total):
        self.progress["value"] = (current / total) * 100
        self.lbl_progress.config(text=f"{current} / {total}")

    def _finish_progress(self, total, errors):
        self.is_busy = False
        self.btn_convert.config(state="normal")
        if errors:
            self.lbl_status.config(text="Completed with errors.")
            msg = ("Conversion finished with errors.\n\n"
                   f"{len(errors)} of {total} item(s) failed.\n\n"
                   f"First error:\n{errors[0][0]}\n{errors[0][1]}")
            messagebox.showwarning("Completed with errors", msg)
        else:
            self.lbl_status.config(text="Completed.")
            messagebox.showinfo("Done", f"All {total} image(s) converted successfully!")

    # ------------- Clear helpers -------------
    def _clear_selected(self):
        if self.is_busy:
            return
        self.file_paths.clear()
        self.folder_paths.clear()
        self._update_counts()

    def _clear_output_folder(self):
        if not self.output_dir or not os.path.isdir(self.output_dir):
            messagebox.showinfo("Info", "Output folder is not set.")
            return
        if not messagebox.askyesno("Confirm", "Delete ALL files in output folder?"):
            return
        cnt = 0
        for n in os.listdir(self.output_dir):
            p = os.path.join(self.output_dir, n)
            if os.path.isfile(p):
                try:
                    os.remove(p); cnt += 1
                except:
                    pass
        messagebox.showinfo("Cleared", f"Deleted {cnt} file(s).")
