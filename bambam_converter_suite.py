import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import argparse
import sys

import localization as i18n

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
        # language state
        self.language = tk.StringVar(value=i18n.get_language())

        self.root.title(i18n.t("app.title"))
        self.root.geometry("900x850")  # biraz büyüttüm; advanced açılınca butonlar görünür kalsın
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap("bambam_logo.ico")  # Window icon
        except:
            pass  # Icon bulunamazsa geç

    

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

        # Dinamik pencere boyutlandırma bayrağı
        self.auto_resize_enabled = False

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

        self.notebook.add(self.home_frame, text=i18n.t("tabs.home"))
        self.notebook.add(self.image_frame, text=i18n.t("tabs.image"))
        self.notebook.add(self.sound_frame, text=i18n.t("tabs.sound"))
        self.notebook.add(self.video_frame, text=i18n.t("tabs.video"))
        self.notebook.add(self.document_frame, text=i18n.t("tabs.document"))
        self.notebook.add(self.rename_frame, text=i18n.t("tabs.rename"))

        # Build contents
        self._build_home()
        self.image_tab = ImageTab(self, self.image_frame)
        self.sound_tab = SoundTab(self, self.sound_frame)     # Trim disabled burada
        self.video_tab = VideoTab(self, self.video_frame)     # Original seçeneği eklendi
        self.document_tab = DocumentTab(self, self.document_frame)
        self.rename_tab = BatchRenameTab(self, self.rename_frame)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # İlk layout tamamlandıktan sonra otomatik resize'a izin ver
        self.root.after(0, self._enable_auto_resize)

        # Apply initial language texts
        self._apply_language()

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

    def adjust_size_to_content(self):
        if not getattr(self, "auto_resize_enabled", False):
            return
        self.root.update_idletasks()
        req_h = self.root.winfo_reqheight()
        cur_w = self.root.winfo_width() or self.root.winfo_reqwidth()

        try:
            cur_x = self.root.winfo_x()
            cur_y = self.root.winfo_y()
            self.root.geometry(f"{cur_w}x{req_h}+{cur_x}+{cur_y}")
        except Exception:
            self.root.geometry(f"{cur_w}x{req_h}")

    def _on_tab_changed(self, event):
        self.adjust_size_to_content()

    def _enable_auto_resize(self):
        self.auto_resize_enabled = True

    def _apply_language(self):
        """Update top-level texts for the current language."""
        lang = self.language.get()
        i18n.set_language(lang)

        # window title
        self.root.title(i18n.t("app.title"))

        # notebook tab titles
        try:
            self.notebook.tab(self.home_frame, text=i18n.t("tabs.home"))
            self.notebook.tab(self.image_frame, text=i18n.t("tabs.image"))
            self.notebook.tab(self.sound_frame, text=i18n.t("tabs.sound"))
            self.notebook.tab(self.video_frame, text=i18n.t("tabs.video"))
            self.notebook.tab(self.document_frame, text=i18n.t("tabs.document"))
            self.notebook.tab(self.rename_frame, text=i18n.t("tabs.rename"))
        except Exception:
            pass

        # Home page labels/buttons
        try:
            if hasattr(self, "lbl_lang"):
                self.lbl_lang.config(text=i18n.t("home.language_label"))
            if hasattr(self, "lbl_home_title"):
                self.lbl_home_title.config(text=i18n.t("home.title"))
            if hasattr(self, "lbl_home_version"):
                self.lbl_home_version.config(text=i18n.t("home.version", version="1.2.8"))
            if hasattr(self, "lbl_home_product"):
                self.lbl_home_product.config(text=i18n.t("home.product"))
            if hasattr(self, "btn_home_image"):
                self.btn_home_image.config(text=i18n.t("home.btn.image"))
            if hasattr(self, "btn_home_sound"):
                self.btn_home_sound.config(text=i18n.t("home.btn.sound"))
            if hasattr(self, "btn_home_video"):
                self.btn_home_video.config(text=i18n.t("home.btn.video"))
            if hasattr(self, "btn_home_document"):
                self.btn_home_document.config(text=i18n.t("home.btn.document"))
            if hasattr(self, "btn_home_rename"):
                self.btn_home_rename.config(text=i18n.t("home.btn.rename"))
        except Exception:
            pass

        # Let tabs refresh their own labels if they implement it
        for tab in (getattr(self, "image_tab", None),
                    getattr(self, "sound_tab", None),
                    getattr(self, "video_tab", None),
                    getattr(self, "document_tab", None),
                    getattr(self, "rename_tab", None)):
            if tab is not None and hasattr(tab, "refresh_language"):
                try:
                    tab.refresh_language()
                except Exception:
                    pass

    def _build_home(self):
        import os
        from PIL import Image, ImageTk
        # For Pyinstaller
        import sys
        if hasattr(sys, '_MEIPASS'):
            LOGO_PATH = os.path.join(sys._MEIPASS, "bambam_logo.png")
        else:
            LOGO_PATH = "bambam_logo.png"

        wrap = ttk.Frame(self.home_frame)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)

        # main center content stays in row 0
        center = ttk.Frame(wrap)
        center.grid(row=0, column=0)

        # language selector (top-right, overlay using place so it doesn't push content down)
        lang_wrap = ttk.Frame(wrap)
        self.lbl_lang = ttk.Label(lang_wrap, text=i18n.t("home.language_label"))
        self.lbl_lang.pack(side="left", padx=(0, 4))
        # display names for languages
        self.language_display = tk.StringVar(value=i18n.get_language_name(self.language.get()))
        lang_names = [i18n.get_language_name(code) for code in i18n.get_available_languages()]
        cb = ttk.Combobox(lang_wrap, state="readonly", textvariable=self.language_display, values=lang_names, width=12)
        cb.pack(side="left")

        def _on_lang_change(event=None):
            code = i18n.get_language_code(self.language_display.get())
            self.language.set(code)
            self._apply_language()

        cb.bind("<<ComboboxSelected>>", _on_lang_change)
        # place in top-right corner with some margin
        lang_wrap.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

        # Logo (varsa)
        self._logo_img = None
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH); img.thumbnail((240, 240), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(center, image=self._logo_img, bg=self.frame_bg).pack(pady=(16, 12))
            except Exception:
                pass

        self.lbl_home_title = ttk.Label(center, text=i18n.t("home.title"), font=("Segoe UI", 16, "bold"))
        self.lbl_home_title.pack()
        self.lbl_home_version = ttk.Label(center, text=i18n.t("home.version", version="1.2.8"))
        self.lbl_home_version.pack(pady=(2, 10))
        self.lbl_home_product = ttk.Label(center, text=i18n.t("home.product"))
        self.lbl_home_product.pack(pady=(0, 16))

        btns = ttk.Frame(center)
        btns.pack(pady=(6, 8))
        self.btn_home_image = ttk.Button(btns, text=i18n.t("home.btn.image"),
                                         command=lambda: self.notebook.select(self.image_frame))
        self.btn_home_image.pack(side="left", padx=8)
        self.btn_home_sound = ttk.Button(btns, text=i18n.t("home.btn.sound"),
                                         command=lambda: self.notebook.select(self.sound_frame))
        self.btn_home_sound.pack(side="left", padx=8)
        self.btn_home_video = ttk.Button(btns, text=i18n.t("home.btn.video"),
                                         command=lambda: self.notebook.select(self.video_frame))
        self.btn_home_video.pack(side="left", padx=8)
        self.btn_home_document = ttk.Button(btns, text=i18n.t("home.btn.document"),
                                            command=lambda: self.notebook.select(self.document_frame))
        self.btn_home_document.pack(side="left", padx=8)
        self.btn_home_rename = ttk.Button(btns, text=i18n.t("home.btn.rename"),
                                          command=lambda: self.notebook.select(self.rename_frame))
        self.btn_home_rename.pack(side="left", padx=8)

    @staticmethod
    def cli_convert(src, fmt, out_dir):
        import os
        from PIL import Image

        os.makedirs(out_dir, exist_ok=True)

        # Determine type by extension
        ext = os.path.splitext(src)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff']:
            # Image convert
            with Image.open(src) as img:
                base = os.path.splitext(os.path.basename(src))[0]
                out = os.path.join(out_dir, f"{base}.{fmt}")
                img.save(out)
                print(f"Converted {src} to {out}")
        elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            # Video (simple copy for now)
            # Assume ffmpeg
            try:
                import subprocess
                cmd = ["ffmpeg", "-y", "-i", src, "-c", "copy", os.path.join(out_dir, f"{os.path.splitext(os.path.basename(src))[0]}.{fmt}")]
                subprocess.run(cmd, check=True)
                print(f"Converted {src}")
            except Exception as e:
                print(f"Error: {e}")
        elif ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']:
            # Sound
            try:
                import subprocess
                bitrate = "192k"  # default
                cmd = ["ffmpeg", "-y", "-i", src, "-b:a", bitrate, os.path.join(out_dir, f"{os.path.splitext(os.path.basename(src))[0]}.{fmt}")]
                subprocess.run(cmd, check=True)
                print(f"Converted {src}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Unsupported file type")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bambam Converter Suite')
    parser.add_argument('--convert', help='Convert file path', type=str)
    parser.add_argument('--to', help='Target format', type=str)
    parser.add_argument('--output', help='Output directory', type=str, default='done')

    args = parser.parse_args()

    if args.convert:
        # CLI mode
        BambamConverterSuite.cli_convert(args.convert, args.to, args.output)
    else:
        # GUI mode
        if TkinterDnD is not None:
            root = TkinterDnD.Tk()
        else:
            import tkinter as tk
            root = tk.Tk()

        app = BambamConverterSuite(root)
        root.mainloop()
