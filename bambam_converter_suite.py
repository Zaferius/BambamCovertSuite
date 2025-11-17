import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

# Optional drag & drop root
try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None

from image_tab import ImageTab
from sound_tab import SoundTab
from video_tab import VideoTab
from document_tab import DocumentTab  # sende zaten vardı
from batch_rename_tab import BatchRenameTab

class BambamConverterSuite:
    def __init__(self, root):
        self.root = root
        self.root.title("Bambam Converter Suite")
        self.root.geometry("900x760")  # biraz büyüttüm; advanced açılınca butonlar görünür kalsın
        self.root.resizable(False, False)

    

        # ---- THEME ----
        self.root_bg = "#14051f"
        self.frame_bg = "#1c0a2a"
        self.fg = "#ffffff"
        self.accent = "#b44dff"
        self.border = "#3d214f"
        self.button_bg = "#2a0f3b"
        self.button_hover = "#35124c"
        self.entry_bg = "#2a0f3b"
        self._setup_style()

        # Notebook (main tabs)
        self.notebook = ttk.Notebook(self.root, style="Bambam.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=4, pady=4)

        # Tabs
        self.home_frame = ttk.Frame(self.notebook)
        self.image_frame = ttk.Frame(self.notebook)
        self.sound_frame = ttk.Frame(self.notebook)
        self.video_frame = ttk.Frame(self.notebook)
        self.document_frame = ttk.Frame(self.notebook)
        self.rename_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.home_frame, text="Home")
        self.notebook.add(self.image_frame, text="Image")
        self.notebook.add(self.sound_frame, text="Sound")
        self.notebook.add(self.video_frame, text="Video")
        self.notebook.add(self.document_frame, text="Document")
        self.notebook.add(self.rename_frame, text="Batch Rename")

        # Build contents
        self._build_home()
        self.image_tab = ImageTab(self, self.image_frame)
        self.sound_tab = SoundTab(self, self.sound_frame)     # Trim disabled burada
        self.video_tab = VideoTab(self, self.video_frame)     # Original seçeneği eklendi
        self.document_tab = DocumentTab(self, self.document_frame)
        self.rename_tab = BatchRenameTab(self, self.rename_frame)

    def _setup_style(self):
        self.root.configure(bg=self.root_bg)
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10, weight="bold")
        self.title_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=self.frame_bg)
        style.configure("TLabelframe", background=self.frame_bg, foreground=self.fg, bordercolor=self.border)
        style.configure("TLabelframe.Label", background=self.frame_bg, foreground=self.fg, font=self.title_font)
        style.configure("TLabel", background=self.frame_bg, foreground=self.fg)

        style.configure("TButton", background=self.button_bg, foreground=self.fg,
                        bordercolor=self.border, focusthickness=1, focuscolor=self.accent, padding=6)
        style.map("TButton", background=[("active", self.button_hover)])

        style.configure("Horizontal.TProgressbar", troughcolor="#1b0b29", background=self.accent,
                        bordercolor=self.border, darkcolor=self.accent, lightcolor=self.accent)

        style.configure("TCheckbutton", background=self.frame_bg, foreground=self.fg)
        style.map("TCheckbutton", background=[("active", self.frame_bg)], foreground=[("active", self.fg)])

        # Main tabs
        style.configure("Bambam.TNotebook", background=self.frame_bg, borderwidth=0)
        style.configure("Bambam.TNotebook.Tab", background=self.button_bg, foreground=self.fg, padding=(10, 5))
        style.map("Bambam.TNotebook.Tab",
                  background=[("selected", self.frame_bg)],
                  foreground=[("selected", self.fg)])

    def _build_home(self):
        import os
        from PIL import Image, ImageTk
        LOGO_PATH = "bambam_logo.png"

        wrap = ttk.Frame(self.home_frame)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)

        center = ttk.Frame(wrap)
        center.grid(row=0, column=0)

        # Logo (varsa)
        self._logo_img = None
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH); img.thumbnail((240, 240), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(center, image=self._logo_img, bg=self.frame_bg).pack(pady=(16, 12))
            except Exception:
                pass

        ttk.Label(center, text="Bambam Converter Suite", font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(center, text="Version 1.2.7").pack(pady=(2, 10))
        ttk.Label(center, text="© Bambam Product 2025").pack(pady=(0, 16))

        btns = ttk.Frame(center)
        btns.pack(pady=(6, 8))
        ttk.Button(btns, text="Open Image Converter",
                   command=lambda: self.notebook.select(self.image_frame)).pack(side="left", padx=8)
        ttk.Button(btns, text="Open Sound Converter",
                   command=lambda: self.notebook.select(self.sound_frame)).pack(side="left", padx=8)
        ttk.Button(btns, text="Open Video Converter",
                   command=lambda: self.notebook.select(self.video_frame)).pack(side="left", padx=8)
        ttk.Button(btns, text="Open Batch Rename",
                   command=lambda: self.notebook.select(self.rename_frame)).pack(side="left", padx=8)


if __name__ == "__main__":
    if TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        import tkinter as tk
        root = tk.Tk()

    app = BambamConverterSuite(root)
    root.mainloop()
