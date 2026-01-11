import os
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

import localization as i18n

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

        self.resize_enabled = tk.BooleanVar(value=False)
        self.resize_width = tk.StringVar(value="")
        self.resize_height = tk.StringVar(value="")
        self.resize_mode = tk.StringVar(value="fit_pad")

        self.rename_enabled = tk.BooleanVar(value=False)
        self.rename_pattern = tk.StringVar(value="{name}_converted_{index}")

        # yeni: mirror & delete
        self.mirror_to_source = tk.BooleanVar(value=True)
        self.delete_originals = tk.BooleanVar(value=False)

        self.drop_canvas = None
        self.lbl_hint = None
        self.is_busy = False

        # presets (temporarily disabled)
        self.presets_enabled = False
        self.presets = {}
        self.presets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_presets.json")

        self._build_ui()
        self._setup_drag_and_drop()
        if self.presets_enabled:
            self._load_presets()

    # ---------------- UI ----------------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}
        main = ttk.Frame(self.parent)
        main.pack(fill="both", expand=True, padx=8, pady=8)
        
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

        self.lbl_title = ttk.Label(main, text=i18n.t("image.title"),
                                   font=("Segoe UI", 12, "bold"))
        self.lbl_title.pack(pady=(0, 8))

        # 1) Select images (drop zone)
        self.lf_select = ttk.LabelFrame(main, text=i18n.t("image.section.select"))
        files = self.lf_select
        files.pack(fill="x", **pad)

        self.drop_canvas = tk.Canvas(files, bg=self.app.frame_bg,
                                     highlightthickness=0, height=120)
        self.drop_canvas.pack(fill="x", padx=6, pady=6)
        self.drop_canvas.bind("<Configure>", self._on_drop_canvas_resize)

        inner = ttk.Frame(self.drop_canvas)
        self.drop_canvas.create_window(10, 10, window=inner, anchor="nw")

        top = ttk.Frame(inner)
        top.pack(fill="x")

        self.btn_browse = ttk.Button(top, text=i18n.t("image.btn.browse_files"), command=self.select_files)
        self.btn_browse.pack(side="left", padx=(0, 8), pady=2)

        self.btn_add_folder = ttk.Button(top, text=i18n.t("image.btn.add_folder"), command=self.add_folder)
        self.btn_add_folder.pack(side="left", padx=(0, 8), pady=2)

        self.lbl_file_count = ttk.Label(top, text=i18n.t("image.files.count", file_count=0, folder_count=0))
        self.lbl_file_count.pack(side="left", pady=2)
        self.btn_clear_selected = ttk.Button(top, text=i18n.t("image.btn.clear_selected"), command=self._clear_selected)
        self.btn_clear_selected.pack(side="right", padx=6)

        self.lbl_hint = ttk.Label(
            inner,
            text=i18n.t("image.hint.dragdrop"),
            wraplength=460,
            justify="left",
        )
        self.lbl_hint.pack(fill="x", anchor="w", pady=(6, 4))

        # 2) Output location
        self.lf_output = ttk.LabelFrame(main, text=i18n.t("image.section.output"))
        out = self.lf_output
        out.pack(fill="x", **pad)

        self.radio_var = tk.StringVar(value="mirror" if self.mirror_to_source.get() else "folder")

        # radio: use folder (üstte, browse button yanında)
        row1 = ttk.Frame(out); row1.pack(fill="x", padx=6, pady=(6, 2))
        self.rb_folder = ttk.Radiobutton(row1, text=i18n.t("image.output.radio.folder"),
                                         value="folder", variable=self.radio_var,
                                         command=self._on_output_mode_change)
        self.rb_folder.pack(side="left")
        self.rb_folder.configure(style="White.TRadiobutton")
        self.btn_output_browse = ttk.Button(row1, text=i18n.t("image.output.btn.browse"), command=self.select_output_dir)
        self.btn_output_browse.pack(side="left", padx=(12, 8))
        self.lbl_output_dir = ttk.Label(row1, text=i18n.t("image.output.label.not_selected"))
        self.lbl_output_dir.configure(foreground="#c7b2ff")
        self.lbl_output_dir.pack(side="left", padx=(6, 0))
        self.btn_output_clear = ttk.Button(row1, text=i18n.t("image.output.btn.clear"), command=self._clear_output_folder)
        self.btn_output_clear.pack(side="right", padx=6)

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

        # 3) Target format + quality
        self.lf_format = ttk.LabelFrame(main, text=i18n.t("image.section.format"))
        fmt = self.lf_format
        fmt.pack(fill="x", **pad)
        ttk.Label(fmt, text=i18n.t("image.format.label")).pack(side="left", padx=5, pady=5)

        options = list(IMAGE_FORMAT_MAP.keys())
        self.format_menu = tk.OptionMenu(fmt, self.target_format, *options, command=self.on_format_selected)
        self.format_menu.pack(side="left", padx=5, pady=5)
        self._style_optionmenu(self.format_menu)

        self.frame_quality = ttk.Frame(fmt)
        self.frame_quality.pack(side="left", padx=15, pady=5)
        self.lbl_quality = ttk.Label(self.frame_quality, text=i18n.t("image.quality.label"))
        self.lbl_quality.pack(side="left", padx=(0, 5))
        self.lbl_quality_value = ttk.Label(self.frame_quality, text=f"{self.quality_var.get()}")
        self.lbl_quality_value.pack(side="right", padx=(5, 0))
        self.quality_scale = ttk.Scale(
            self.frame_quality, from_=40, to=100, orient="horizontal",
            variable=self.quality_var, command=lambda v: self.update_quality_label(),
            length=150
        )
        self.quality_scale.pack(side="right")

        # 4) Resize (optional)
        self.lf_resize = ttk.LabelFrame(main, text=i18n.t("image.section.resize"))
        resize = self.lf_resize
        resize.pack(fill="x", **pad)
        self.chk_resize_enable = ttk.Checkbutton(resize, text=i18n.t("image.resize.enable"),
                                                 variable=self.resize_enabled, command=self.on_resize_toggle)
        self.chk_resize_enable.pack(anchor="w", padx=5, pady=3)
        self.resize_content = ttk.Frame(resize)
        row_r1 = ttk.Frame(self.resize_content); row_r1.pack(fill="x", padx=5, pady=(0, 5))
        self.lbl_resize_w = ttk.Label(row_r1, text=i18n.t("image.resize.width"))
        self.lbl_resize_w.pack(side="left", padx=(0, 5))
        self.entry_resize_w = tk.Entry(
            row_r1, textvariable=self.resize_width,
            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"
        )
        self.entry_resize_w.pack(side="left", padx=(0, 10))
        self.lbl_resize_h = ttk.Label(row_r1, text=i18n.t("image.resize.height"))
        self.lbl_resize_h.pack(side="left", padx=(0, 5))
        self.entry_resize_h = tk.Entry(
            row_r1, textvariable=self.resize_height,
            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"
        )
        self.entry_resize_h.pack(side="left")

        row_r2 = ttk.Frame(self.resize_content); row_r2.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Radiobutton(row_r2, text=i18n.t("image.resize.mode.fit_pad"),
                        variable=self.resize_mode, value="fit_pad")\
            .pack(side="left", padx=(0, 10))
        ttk.Radiobutton(row_r2, text=i18n.t("image.resize.mode.stretch"),
                        variable=self.resize_mode, value="stretch")\
            .pack(side="left")

        # 5) Batch rename
        self.lf_rename = ttk.LabelFrame(main, text=i18n.t("image.section.rename"))
        rename = self.lf_rename
        rename.pack(fill="x", **pad)
        self.chk_rename_enable = ttk.Checkbutton(rename, text=i18n.t("image.rename.enable"),
                                                 variable=self.rename_enabled, command=self.on_rename_toggle)
        self.chk_rename_enable.pack(anchor="w", padx=5, pady=3)
        self.rename_content = ttk.Frame(rename)
        row = ttk.Frame(self.rename_content); row.pack(fill="x", padx=5, pady=(0, 5))
        self.lbl_pattern = ttk.Label(row, text=i18n.t("image.rename.pattern"))
        self.lbl_pattern.pack(side="left", padx=(0, 5))
        self.entry_pattern = tk.Entry(
            row, textvariable=self.rename_pattern,
            bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat"
        )
        self.entry_pattern.pack(side="left", fill="x", expand=True)
        self.lbl_rename_hint = ttk.Label(
            self.rename_content,
            text=i18n.t("image.rename.hint"),
        )
        self.lbl_rename_hint.pack(anchor="w", padx=5, pady=(0, 3))
        self.on_resize_toggle()
        self.on_rename_toggle()

        # 5) Progress
        self.lf_progress = ttk.LabelFrame(main, text=i18n.t("image.section.progress"))
        prog = self.lf_progress
        prog.pack(fill="x", **pad)
        
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
        self.lbl_progress = ttk.Label(overall_prog_frame, text=i18n.t("image.progress.initial"), font=("", 8))
        self.lbl_progress.pack(anchor="w", pady=(0, 1))
        self.progress = ttk.Progressbar(overall_prog_frame, mode="determinate")
        self.progress.pack(fill="x", ipady=8)
        
        self.lbl_status = ttk.Label(prog, text=i18n.t("image.status.idle"))
        self.lbl_status.pack(pady=(2, 4))

        # 6) Actions
        actions = ttk.Frame(main); actions.pack(pady=10)
        self.btn_convert = ttk.Button(actions, text=i18n.t("image.btn.start"), command=self.start_conversion)
        self.btn_convert.pack(side="left", padx=6)

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
        folders = []
        while True:
            d = filedialog.askdirectory(title="Select folder")
            if not d:
                break
            folders.append(d)
            if not messagebox.askyesno("Add another folder?", "Do you want to add another folder?"):
                break
        if folders:
            self.folder_paths.extend(folders)
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
        self.btn_output_browse.configure(state=state)
        self.btn_output_clear.configure(state=state)
        
        # Update label visibility and text
        if use_mirror:
            # Hide the output folder label when using mirror mode
            self.lbl_output_dir.pack_forget()
        else:
            # Show the output folder label
            if not self.lbl_output_dir.winfo_ismapped():
                self.lbl_output_dir.pack(side="left", padx=(6, 0))
            if self.output_dir:
                text = self.output_dir if len(self.output_dir) <= 45 else "..." + self.output_dir[-45:]
                self.lbl_output_dir.configure(text=text, foreground=self.app.fg)
            else:
                self.lbl_output_dir.configure(text=i18n.t("image.output.label.not_selected"), foreground="#c7b2ff")
        
        # "Original" + delete originals kombinasyonunda guard
        self._update_delete_guard()

    # ------------- Presets -------------
    def _load_presets(self):
        if not self.presets_enabled:
            self.presets = {}
            return
        try:
            if os.path.exists(self.presets_path):
                with open(self.presets_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.presets = data
        except Exception:
            self.presets = {}

    def _save_presets(self):
        if not self.presets_enabled:
            return
        try:
            with open(self.presets_path, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=2)
        except Exception:
            messagebox.showwarning(i18n.t("image.presets.warning.title"), i18n.t("image.presets.warning.save_failed"))

    def _open_presets_window(self):
        if not self.presets_enabled:
            return
        if hasattr(self, "presets_win") and self.presets_win is not None and tk.Toplevel.winfo_exists(self.presets_win):
            self.presets_win.lift()
            return

        self.presets_win = tk.Toplevel(self.root)
        self.presets_win.title(i18n.t("image.presets.window_title"))
        try:
            import sys
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, "bambam_logo.ico")
            else:
                icon_path = "bambam_logo.ico"
            self.presets_win.iconbitmap(icon_path)
        except Exception:
            pass
        try:
            self.presets_win.configure(bg=self.app.root_bg)
        except Exception:
            pass

        frm = ttk.Frame(self.presets_win)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        list_frame = ttk.Frame(frm); list_frame.pack(fill="both", expand=True)
        self.lbl_presets_list = ttk.Label(list_frame, text=i18n.t("image.presets.label_list"))
        self.lbl_presets_list.pack(anchor="w")
        self.lst_presets = tk.Listbox(list_frame, height=8)
        self.lst_presets.pack(fill="both", expand=True, pady=(2, 6))

        # name entry + buttons
        bottom = ttk.Frame(frm); bottom.pack(fill="x", pady=(4, 0))
        self.lbl_preset_name = ttk.Label(bottom, text=i18n.t("image.presets.label_name"))
        self.lbl_preset_name.pack(side="left")
        self.preset_name_var = tk.StringVar()
        tk.Entry(bottom, textvariable=self.preset_name_var,
                 bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat", width=20)
        self.entry_preset_name = tk.Entry(bottom, textvariable=self.preset_name_var,
                                          bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat", width=20)
        self.entry_preset_name.pack(side="left", padx=(4, 8))

        btns = ttk.Frame(frm); btns.pack(fill="x", pady=(6, 0))
        self.btn_preset_apply = ttk.Button(btns, text=i18n.t("image.presets.btn.apply"), command=self._apply_selected_preset)
        self.btn_preset_apply.pack(side="right", padx=4)
        self.btn_preset_delete = ttk.Button(btns, text=i18n.t("image.presets.btn.delete"), command=self._delete_selected_preset)
        self.btn_preset_delete.pack(side="right", padx=4)
        self.btn_preset_add = ttk.Button(btns, text=i18n.t("image.presets.btn.add"), command=self._add_current_as_preset)
        self.btn_preset_add.pack(side="right", padx=4)

        self._refresh_presets_list()

    def _refresh_presets_list(self):
        if not self.presets_enabled:
            return
        if not hasattr(self, "lst_presets"):
            return
        self.lst_presets.delete(0, tk.END)
        for name in sorted(self.presets.keys()):
            self.lst_presets.insert(tk.END, name)

    def _get_selected_preset_name(self):
        if not self.presets_enabled:
            return None
        if not hasattr(self, "lst_presets"):
            return None
        sel = self.lst_presets.curselection()
        if not sel:
            return None
        return self.lst_presets.get(sel[0])

    def _add_current_as_preset(self):
        if not self.presets_enabled:
            return
        name = self.preset_name_var.get().strip()
        if not name:
            messagebox.showwarning(i18n.t("image.presets.warning.title"), i18n.t("image.presets.warning.no_name"))
            return

        # collect current settings
        try:
            w = int(self.resize_width.get() or "0")
            h = int(self.resize_height.get() or "0")
        except Exception:
            w = 0; h = 0

        preset = {
            "format": self.target_format.get(),
            "width": w,
            "height": h,
            "output_dir": self.output_dir,
            "rename_pattern": self.rename_pattern.get(),
        }
        self.presets[name] = preset
        self._save_presets()
        self._refresh_presets_list()

    def _delete_selected_preset(self):
        if not self.presets_enabled:
            return
        name = self._get_selected_preset_name()
        if not name:
            return
        if messagebox.askyesno(i18n.t("image.presets.confirm.delete_title"), i18n.t("image.presets.confirm.delete_message", name=name)):
            self.presets.pop(name, None)
            self._save_presets()
            self._refresh_presets_list()

    def _apply_selected_preset(self):
        if not self.presets_enabled:
            return
        name = self._get_selected_preset_name()
        if not name:
            return
        preset = self.presets.get(name)
        if not preset:
            return

        # apply format
        fmt = preset.get("format", self.target_format.get())
        if fmt not in IMAGE_FORMAT_MAP:
            fmt = self.target_format.get()
        self.target_format.set(fmt)
        self.on_format_selected(fmt)

        # apply resize
        w = preset.get("width", 0) or 0
        h = preset.get("height", 0) or 0
        if w > 0 and h > 0:
            self.resize_enabled.set(True)
            self.resize_width.set(str(w))
            self.resize_height.set(str(h))
            self.on_resize_toggle()
        else:
            self.resize_enabled.set(False)
            self.on_resize_toggle()

        # apply output dir
        out = preset.get("output_dir", "")
        if out:
            self.output_dir = out
            short = out if len(out) <= 45 else "..." + out[-45:]
            self.lbl_output_dir.config(text=short, foreground=self.app.fg)

        # apply rename pattern
        pat = preset.get("rename_pattern")
        if pat:
            self.rename_pattern.set(pat)
            self.rename_enabled.set(True)
            self.on_rename_toggle()

        if hasattr(self.app, "adjust_size_to_content"):
            self.app.adjust_size_to_content()

    # ------------- Localization refresh -------------
    def refresh_language(self):
        """Refresh visible texts according to current language."""
        # Header
        self.lbl_title.config(text=i18n.t("image.title"))
        self.btn_presets.config(text=i18n.t("image.header.presets"))

        # Top row buttons
        self.btn_browse.config(text=i18n.t("image.btn.browse_files"))
        self.btn_add_folder.config(text=i18n.t("image.btn.add_folder"))
        self.btn_clear_selected.config(text=i18n.t("image.btn.clear_selected"))

        # Sections
        self.lf_select.config(text=i18n.t("image.section.select"))
        self.lf_output.config(text=i18n.t("image.section.output"))
        self.lf_format.config(text=i18n.t("image.section.format"))
        self.lf_resize.config(text=i18n.t("image.section.resize"))
        self.lf_rename.config(text=i18n.t("image.section.rename"))
        self.lf_progress.config(text=i18n.t("image.section.progress"))

        # Buttons / labels that don't depend on counts
        self.lbl_hint.config(text=i18n.t("image.hint.dragdrop"))
        self.rb_mirror.config(text=i18n.t("image.output.radio.mirror"))
        self.rb_folder.config(text=i18n.t("image.output.radio.folder"))
        self.chk_delete_originals.config(text=i18n.t("image.output.delete_originals"))
        self.btn_output_browse.config(text=i18n.t("image.output.btn.browse"))
        self.btn_output_clear.config(text=i18n.t("image.output.btn.clear"))
        self.lbl_output_dir.config(
            text=i18n.t("image.output.label.not_selected")
            if not self.output_dir and not self.mirror_to_source.get()
            else (i18n.t("image.output.label.using_source") if self.mirror_to_source.get() else self.lbl_output_dir.cget("text"))
        )
        self.lbl_quality.config(text=i18n.t("image.quality.label"))
        self.lbl_resize_w.config(text=i18n.t("image.resize.width"))
        self.lbl_resize_h.config(text=i18n.t("image.resize.height"))
        self.chk_resize_enable.config(text=i18n.t("image.resize.enable"))
        self.lbl_pattern.config(text=i18n.t("image.rename.pattern"))
        self.lbl_rename_hint.config(text=i18n.t("image.rename.hint"))
        self.chk_rename_enable.config(text=i18n.t("image.rename.enable"))
        self.lbl_status.config(text=i18n.t("image.status.idle"))
        self.btn_convert.config(text=i18n.t("image.btn.start"))

        # Recompute counts string
        self._update_counts()

        # If presets window is open, refresh its labels/buttons
        if hasattr(self, "presets_win") and self.presets_win is not None and tk.Toplevel.winfo_exists(self.presets_win):
            self.presets_win.title(i18n.t("image.presets.window_title"))
            self.lbl_presets_list.config(text=i18n.t("image.presets.label_list"))
            self.lbl_preset_name.config(text=i18n.t("image.presets.label_name"))
            self.btn_preset_apply.config(text=i18n.t("image.presets.btn.apply"))
            self.btn_preset_delete.config(text=i18n.t("image.presets.btn.delete"))
            self.btn_preset_add.config(text=i18n.t("image.presets.btn.add"))

    # ------------- Helpers -------------
    def _dedupe_inputs(self):
        self.file_paths = list(dict.fromkeys(self.file_paths))
        self.folder_paths = list(dict.fromkeys(self.folder_paths))

    def _update_counts(self):
        self.lbl_file_count.config(
            text=i18n.t("image.files.count", file_count=len(self.file_paths), folder_count=len(self.folder_paths))
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

    def _maybe_resize_image(self, img):
        if not self.resize_enabled.get():
            return img
        w, h = img.size
        try:
            tw = int(self.resize_width.get() or "0")
        except Exception:
            tw = 0
        try:
            th = int(self.resize_height.get() or "0")
        except Exception:
            th = 0
        if tw <= 0 or th <= 0:
            return img
        tw = min(tw, w)
        th = min(th, h)
        if tw <= 0 or th <= 0:
            return img
        mode = self.resize_mode.get()
        if mode == "stretch":
            if (tw, th) == (w, h):
                return img
            return img.resize((tw, th), Image.LANCZOS)
        scale = min(tw / w, th / h, 1.0)
        if scale >= 1.0:
            return img
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        if img.mode != "RGB":
            work = img.convert("RGB")
        else:
            work = img
        resized = work.resize((new_w, new_h), Image.LANCZOS)
        bg = Image.new("RGB", (tw, th), (255, 255, 255))
        x = (tw - new_w) // 2
        y = (th - new_h) // 2
        bg.paste(resized, (x, y))
        return bg

    def on_rename_toggle(self):
        if self.rename_enabled.get():
            self.rename_content.pack(fill="x", padx=0, pady=(0, 5))
        else:
            self.rename_content.pack_forget()
        if hasattr(self.app, "adjust_size_to_content"):
            self.app.adjust_size_to_content()

    def on_resize_toggle(self):
        if self.resize_enabled.get():
            self.resize_content.pack(fill="x", padx=0, pady=(0, 5))
        else:
            self.resize_content.pack_forget()
        if hasattr(self.app, "adjust_size_to_content"):
            self.app.adjust_size_to_content()

    # ------------- Conversion -------------
    def start_conversion(self):
        if self.is_busy:
            return
        if not self.file_paths and not self.folder_paths:
            messagebox.showwarning(i18n.t("image.warning.title"), i18n.t("image.warning.no_selection"))
            return
        if not self.mirror_to_source.get() and not self.output_dir:
            messagebox.showwarning(i18n.t("image.warning.title"), i18n.t("image.warning.no_output"))
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
            messagebox.showinfo(i18n.t("image.info.title"), i18n.t("image.info.no_images"))
            return

        self.is_busy = True
        self.btn_convert.config(state="disabled")
        self.progress["value"] = 0
        self.file_progress["value"] = 0
        self.lbl_progress.config(text=f"Overall: 0 / {len(jobs)}")
        self.lbl_file_prog.config(text="")
        self.lbl_status.config(text=i18n.t("image.status.processing"))

        threading.Thread(target=self._convert_worker, args=(jobs,), daemon=True).start()

    def _convert_worker(self, jobs):
        total = len(jobs)
        errors = []

        fmt_key = self.target_format.get().upper()
        pil_format, ext = IMAGE_FORMAT_MAP.get(fmt_key, ("PNG", "png"))

        idx = 0
        last_output_dir = None
        for i, src_path in enumerate(jobs, start=1):
            # Update file progress
            filename = os.path.basename(src_path)
            self.root.after(0, lambda f=filename: self.lbl_file_prog.config(text=f"Processing: {f}"))
            self.root.after(0, lambda: self.file_progress.config(value=0))
            
            try:
                src_dir = os.path.dirname(src_path)
                # çıkış klasörü
                out_dir = src_dir if self.mirror_to_source.get() else self.output_dir

                with Image.open(src_path) as img:
                    if pil_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")

                    img = self._maybe_resize_image(img)

                    if pil_format is None:
                        # Original: sadece kopyala (Pillow üzerinden yeniden kaydet)
                        orig_ext = os.path.splitext(src_path)[1].lstrip(".")
                        base_name = self._build_base_name(src_path, i)
                        out_path = self._avoid_overwrite(os.path.join(out_dir, f"{base_name}.{orig_ext}"))
                        img.save(out_path)
                        # original delete — Original modda güvenlik için devre dışı (guard üstte)
                    else:
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
                        last_output_dir = os.path.dirname(out_path)

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
            # Set file progress to 100% when done
            self.root.after(0, lambda: self.file_progress.config(value=100))
            self.root.after(0, self._tick_progress, idx, total)

        self.root.after(0, self._finish_progress, total, errors, last_output_dir)

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
        self.lbl_progress.config(text=f"Overall: {current} / {total}")

    def _finish_progress(self, total, errors, last_output_dir=None):
        self.is_busy = False
        self.btn_convert.config(state="normal")
        if errors:
            self.lbl_status.config(text=i18n.t("image.result.errors_status"))
            first = errors[0]
            msg = i18n.t(
                "image.result.errors_message",
                failed=len(errors),
                total=total,
                path=first[0],
                error=first[1],
            )
            messagebox.showwarning(i18n.t("image.result.errors_title"), msg)
        else:
            self.lbl_status.config(text=i18n.t("image.result.done_status"))
            messagebox.showinfo(
                i18n.t("image.result.done_title"),
                i18n.t("image.result.done_message", total=total),
            )
            target_dir = last_output_dir or (self.output_dir if not self.mirror_to_source.get() else None)
            if not target_dir and self.mirror_to_source.get() and self.file_paths:
                target_dir = os.path.dirname(self.file_paths[0])
            self.app.open_folder_if_enabled(target_dir)

    # ------------- Clear helpers -------------
    def _clear_selected(self):
        if self.is_busy:
            return
        self.file_paths.clear()
        self.folder_paths.clear()
        self._update_counts()

    def _clear_output_folder(self):
        if not self.output_dir or not os.path.isdir(self.output_dir):
            messagebox.showinfo(i18n.t("image.info.title"), i18n.t("image.clear_output.info_no_folder"))
            return
        if not messagebox.askyesno(i18n.t("image.clear_output.confirm_title"), i18n.t("image.clear_output.confirm_message")):
            return
        cnt = 0
        for n in os.listdir(self.output_dir):
            p = os.path.join(self.output_dir, n)
            if os.path.isfile(p):
                try:
                    os.remove(p); cnt += 1
                except:
                    pass
        messagebox.showinfo(i18n.t("image.clear_output.done_title"), i18n.t("image.clear_output.done_message", count=cnt))
