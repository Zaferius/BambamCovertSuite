import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

from PIL import Image

# Optional drag & drop support
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    TkinterDnD = None
    DND_FILES = None


FORMAT_MAP = {
    "PNG": ("PNG", "png"),
    "JPG": ("JPEG", "jpg"),
    "JPEG": ("JPEG", "jpg"),
    "WEBP": ("WEBP", "webp"),
    "TIFF": ("TIFF", "tiff"),
    "BMP": ("BMP", "bmp"),
    "GIF": ("GIF", "gif"),
}


class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultra Fast Image Converter")
        # Daha da yüksek, sabit boyut: Batch rename açıkken de Start görünsün
        self.root.geometry("540x620")
        self.root.resizable(False, False)

        # ---- THEME & FONT ----
        self._setup_style()

        # State
        self.file_paths = []
        self.output_dir = ""
        self.target_format = tk.StringVar(value="PNG")
        self.quality_var = tk.IntVar(value=90)

        self.rename_enabled = tk.BooleanVar(value=False)
        self.rename_pattern = tk.StringVar(value="{name}_converted_{index}")

        self.drop_canvas = None  # dashed border çizmek için

        self._build_ui()
        self._setup_drag_and_drop()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def _setup_style(self):
        # Purple theme colors
        self.root_bg = "#14051f"
        self.frame_bg = "#1c0a2a"
        self.fg = "#ffffff"
        self.accent = "#b44dff"
        self.border = "#3d214f"
        self.button_bg = "#2a0f3b"
        self.button_hover = "#35124c"
        self.entry_bg = "#2a0f3b"

        self.root.configure(bg=self.root_bg)

        # Global font
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10, weight="bold")

        self.title_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=self.frame_bg)
        style.configure(
            "TLabelframe",
            background=self.frame_bg,
            foreground=self.fg,
            bordercolor=self.border,
        )
        style.configure(
            "TLabelframe.Label",
            background=self.frame_bg,
            foreground=self.fg,
            font=self.title_font,
        )
        style.configure("TLabel", background=self.frame_bg, foreground=self.fg)

        style.configure(
            "TButton",
            background=self.button_bg,
            foreground=self.fg,
            bordercolor=self.border,
            focusthickness=1,
            focuscolor=self.accent,
            padding=6,
        )
        style.map(
            "TButton",
            background=[("active", self.button_hover)],
        )

        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#1b0b29",
            background=self.accent,
            bordercolor=self.border,
            darkcolor=self.accent,
            lightcolor=self.accent,
        )

        style.configure(
            "TScale",
            background=self.frame_bg,
            troughcolor="#1b0b29",
        )

        # Checkbutton theme
        style.configure(
            "TCheckbutton",
            background=self.frame_bg,
            foreground=self.fg,
        )
        style.map(
            "TCheckbutton",
            background=[("active", self.frame_bg)],
            foreground=[("active", self.fg)],
        )

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        padding = {"padx": 10, "pady": 5}

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # 0) Header
        header = ttk.Label(
            main_frame,
            text="Bambam Image Converter",
            font=("Segoe UI", 12, "bold"),
        )
        header.pack(pady=(0, 8))

        # 1) Select images (LabelFrame + dashed drop zone)
        frame_files = ttk.LabelFrame(main_frame, text="1) Select Images")
        frame_files.pack(fill="x", **padding)

        # Canvas: dashed borderlı drop zone
        self.drop_canvas = tk.Canvas(
            frame_files,
            bg=self.frame_bg,
            highlightthickness=0,
            height=90,
        )
        self.drop_canvas.pack(fill="x", padx=6, pady=6)
        self.drop_canvas.bind("<Configure>", self._draw_drop_zone_border)

        # Canvas içine gerçek içerik için bir frame yerleştiriyoruz
        drop_inner = ttk.Frame(self.drop_canvas)
        self.drop_canvas.create_window(10, 10, window=drop_inner, anchor="nw")

        # Üst satır: Browse + counter
        top_row = ttk.Frame(drop_inner)
        top_row.pack(fill="x", pady=(0, 2))

        btn_select = ttk.Button(top_row, text="Browse Images...", command=self.select_files)
        btn_select.pack(side="left", padx=(0, 10), pady=2)

        self.lbl_file_count = ttk.Label(top_row, text="Selected files: 0")
        self.lbl_file_count.pack(side="left", pady=2)

        # Alt satır: drag & drop hint
        self.lbl_hint = ttk.Label(
            drop_inner,
            text="You can also drag & drop files onto this area.",
            wraplength=470,
            justify="left",
        )
        self.lbl_hint.pack(anchor="w", pady=(4, 0))

        # 2) Output folder
        frame_output = ttk.LabelFrame(main_frame, text="2) Select Output Folder")
        frame_output.pack(fill="x", **padding)

        btn_output = ttk.Button(frame_output, text="Browse Folder...", command=self.select_output_dir)
        btn_output.pack(side="left", padx=5, pady=5)

        self.lbl_output_dir = ttk.Label(frame_output, text="Not selected")
        self.lbl_output_dir.configure(foreground="#c7b2ff")
        self.lbl_output_dir.pack(side="left", padx=10)

        # 3) Target format + quality
        frame_format = ttk.LabelFrame(main_frame, text="3) Target Format & Quality")
        frame_format.pack(fill="x", **padding)

        ttk.Label(frame_format, text="Format:").pack(side="left", padx=5, pady=5)

        options = list(FORMAT_MAP.keys())
        self.format_menu = tk.OptionMenu(
            frame_format,
            self.target_format,
            *options,
            command=self.on_format_selected,
        )
        self.format_menu.pack(side="left", padx=5, pady=5)

        self.format_menu.config(
            bg=self.entry_bg,
            fg=self.fg,
            activebackground=self.button_hover,
            activeforeground=self.fg,
            highlightthickness=1,
            highlightbackground=self.border,
            relief="flat",
            font=self.title_font,
        )
        menu = self.format_menu["menu"]
        menu.config(
            bg=self.entry_bg,
            fg=self.fg,
            activebackground=self.button_hover,
            activeforeground=self.fg,
            font=self.title_font,
        )

        # Quality frame (only for JPG/JPEG)
        self.frame_quality = ttk.Frame(frame_format)
        self.frame_quality.pack(side="left", padx=15, pady=5)
        ttk.Label(self.frame_quality, text="JPEG Quality:").pack(side="left", padx=(0, 5))

        self.lbl_quality_value = ttk.Label(self.frame_quality, text=f"{self.quality_var.get()}")
        self.lbl_quality_value.pack(side="right", padx=(5, 0))

        self.quality_scale = ttk.Scale(
            self.frame_quality,
            from_=40,
            to=100,
            orient="horizontal",
            variable=self.quality_var,
            command=lambda v: self.update_quality_label(),
            length=150,
        )
        self.quality_scale.pack(side="right")

        # 4) Batch rename (collapsible)
        frame_rename = ttk.LabelFrame(main_frame, text="4) Batch Rename (optional)")
        frame_rename.pack(fill="x", **padding)

        chk = ttk.Checkbutton(
            frame_rename,
            text="Enable batch renaming",
            variable=self.rename_enabled,
            command=self.on_rename_toggle,
        )
        chk.pack(anchor="w", padx=5, pady=3)

        # İçerik frame’i
        self.rename_content = ttk.Frame(frame_rename)

        # Pattern row
        self.pattern_frame = ttk.Frame(self.rename_content)
        self.pattern_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Label(self.pattern_frame, text="Pattern:").pack(side="left", padx=(0, 5))

        self.entry_pattern = tk.Entry(
            self.pattern_frame,
            textvariable=self.rename_pattern,
            bg=self.entry_bg,
            fg=self.fg,
            insertbackground=self.fg,
            relief="flat",
        )
        self.entry_pattern.pack(side="left", fill="x", expand=True)

        # Help label
        self.help_label = ttk.Label(
            self.rename_content,
            text="Placeholders: {name} = original name, {index} = 1,2,3...",
        )
        self.help_label.pack(anchor="w", padx=5, pady=(0, 3))

        # Başlangıçta gizli
        self.on_rename_toggle()

        # 5) Progress bar
        frame_progress = ttk.LabelFrame(main_frame, text="Progress")
        frame_progress.pack(fill="x", **padding)

        self.progress = ttk.Progressbar(frame_progress, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        self.lbl_progress = ttk.Label(frame_progress, text="0 / 0")
        self.lbl_progress.pack(pady=2)

        # 6) Start button
        frame_actions = ttk.Frame(main_frame)
        frame_actions.pack(fill="x", pady=15)

        self.btn_convert = ttk.Button(frame_actions, text="Start Conversion", command=self.start_conversion)
        self.btn_convert.pack(pady=5)

        # Initial quality visibility
        self.on_format_selected(self.target_format.get())

    # ------------------------------------------------------------------
    # Dashed border çizimi
    # ------------------------------------------------------------------
    def _draw_drop_zone_border(self, event):
        if not self.drop_canvas:
            return
        self.drop_canvas.delete("border")
        margin = 4
        self.drop_canvas.create_rectangle(
            margin,
            margin,
            event.width - margin,
            event.height - margin,
            outline=self.fg,
            dash=(4, 3),
            width=1,
            tags="border",
        )

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------
    def _setup_drag_and_drop(self):
        if TkinterDnD is None or DND_FILES is None:
            return  # optional

        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self.on_drop)
        except Exception:
            pass

    def on_drop(self, event):
        raw = event.data
        paths = self.root.splitlist(raw)

        new_files = []
        for p in paths:
            p = p.strip()
            if os.path.isdir(p):
                for name in os.listdir(p):
                    full = os.path.join(p, name)
                    if os.path.isfile(full) and self.is_image_file(full):
                        new_files.append(full)
            elif os.path.isfile(p) and self.is_image_file(p):
                new_files.append(p)

        if new_files:
            self.file_paths.extend(new_files)
            self.file_paths = list(dict.fromkeys(self.file_paths))
            self.update_file_count()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def is_image_file(self, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in [".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".tiff", ".tif", ".gif"]

    def update_file_count(self):
        self.lbl_file_count.config(text=f"Selected files: {len(self.file_paths)}")

    def update_quality_label(self):
        self.lbl_quality_value.config(text=str(int(self.quality_var.get())))

    def on_format_selected(self, value):
        value = value.upper()
        if value in ("JPG", "JPEG"):
            self.frame_quality.pack(side="left", padx=15, pady=5)
        else:
            self.frame_quality.pack_forget()

    def on_rename_toggle(self):
        if self.rename_enabled.get():
            self.rename_content.pack(fill="x", padx=0, pady=(0, 5))
        else:
            self.rename_content.pack_forget()

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------
    def select_files(self):
        filetypes = [
            ("All Images", "*.png *.jpg *.jpeg *.jfif *.webp *.bmp *.tiff *.tif *.gif"),
            ("PNG", "*.png"),
            ("JPG/JPEG", "*.jpg *.jpeg *.jfif"),
            ("Other", "*.webp *.bmp *.tiff *.tif *.gif"),
        ]
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=filetypes,
        )
        if paths:
            self.file_paths.extend(list(paths))
            self.file_paths = list(dict.fromkeys(self.file_paths))
            self.update_file_count()

    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_dir = directory
            short = directory
            if len(short) > 45:
                short = "..." + short[-45:]
            self.lbl_output_dir.config(text=short, foreground=self.fg)

    def start_conversion(self):
        if not self.file_paths:
            messagebox.showwarning("Warning", "Please select at least one image.")
            return

        if not self.output_dir:
            messagebox.showwarning("Warning", "Please select an output folder.")
            return

        self.progress["value"] = 0
        self.lbl_progress.config(text=f"0 / {len(self.file_paths)}")

        self.btn_convert.config(state="disabled")

        t = threading.Thread(target=self.convert_images, daemon=True)
        t.start()

    # ------------------------------------------------------------------
    # Conversion logic
    # ------------------------------------------------------------------
    def convert_images(self):
        total = len(self.file_paths)
        errors = []

        fmt_key = self.target_format.get().upper()
        pil_format, ext = FORMAT_MAP.get(fmt_key, ("PNG", "png"))

        for idx, path in enumerate(self.file_paths, start=1):
            try:
                with Image.open(path) as img:
                    if pil_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")

                    orig_name = os.path.splitext(os.path.basename(path))[0]

                    if self.rename_enabled.get():
                        try:
                            base_name = self.rename_pattern.get().format(
                                name=orig_name,
                                index=idx,
                            )
                        except Exception:
                            base_name = f"{orig_name}_{idx}"
                    else:
                        base_name = orig_name

                    base_name = base_name.replace(os.sep, "_")
                    out_path = os.path.join(self.output_dir, f"{base_name}.{ext}")
                    out_path = self._avoid_overwrite(out_path)

                    save_kwargs = {}
                    if pil_format == "JPEG":
                        q = int(self.quality_var.get())
                        save_kwargs.update(
                            dict(
                                quality=q,
                                optimize=True,
                                progressive=True,
                            )
                        )
                    elif pil_format == "WEBP":
                        q = int(self.quality_var.get())
                        save_kwargs.update(dict(quality=q, method=6))

                    img.save(out_path, pil_format, **save_kwargs)

            except Exception as e:
                errors.append((path, str(e)))

            self.root.after(0, self.update_progress, idx, total)

        self.root.after(0, self.finish_conversion, total, errors)

    def _avoid_overwrite(self, out_path: str) -> str:
        if not os.path.exists(out_path):
            return out_path
        base, ext = os.path.splitext(out_path)
        counter = 1
        new_path = f"{base}_{counter}{ext}"
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_{counter}{ext}"
        return new_path

    def update_progress(self, current, total):
        percent = (current / total) * 100
        self.progress["value"] = percent
        self.lbl_progress.config(text=f"{current} / {total}")

    def finish_conversion(self, total, errors):
        self.btn_convert.config(state="normal")
        if errors:
            msg = (
                "Conversion finished with errors.\n\n"
                f"{len(errors)} out of {total} file(s) failed.\n\n"
                f"First error:\n{errors[0][0]}\n{errors[0][1]}"
            )
            messagebox.showwarning("Completed with errors", msg)
        else:
            messagebox.showinfo("Done", f"All {total} file(s) converted successfully!")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    if TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = ImageConverterApp(root)
    root.mainloop()
