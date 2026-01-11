# landing_tab.py
import os
import webbrowser
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

LOGO_PATH = "bambam_logo.png"
VERSION = "1.2.9"

class LandingTab:
    def __init__(self, app, parent):
        self.app = app
        self.root = app.root
        self.parent = parent
        self.logo_img = None
        self._build_ui()

    def _build_ui(self):
        # Ana konteyner
        container = tk.Frame(self.parent, bg=self.app.frame_bg)
        container.pack(fill="both", expand=True)

        # Orta içerik
        center = ttk.Frame(container)
        center.pack(expand=True)  # ortala

        # Logo
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img.thumbnail((260, 260), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(center, image=self.logo_img, bg=self.app.frame_bg).pack(pady=(10, 10))
            except Exception:
                self._build_text_logo(center)
        else:
            self._build_text_logo(center)

        ttk.Label(center, text="Bambam Converter Suite", font=("Segoe UI", 14, "bold")).pack(pady=(5, 2))
        ttk.Label(center, text=f"Version {VERSION}").pack(pady=(0, 8))
        ttk.Label(center, text="© Bambam Product 2025").pack(pady=(0, 14))

        # Hızlı erişim butonları
        btns = ttk.Frame(center)
        btns.pack(pady=(4, 6))
        ttk.Button(btns, text="Open Image Converter",
                   command=lambda: self.app.notebook.select(self.app.image_frame)).pack(side="left", padx=8)
        ttk.Button(btns, text="Open Sound Converter",
                   command=lambda: self.app.notebook.select(self.app.sound_frame)).pack(side="left", padx=8)
        if hasattr(self.app, "video_frame"):
            ttk.Button(btns, text="Open Video Converter",
                       command=lambda: self.app.notebook.select(self.app.video_frame)).pack(side="left", padx=8)
        if hasattr(self.app, "batch_frame"):
            ttk.Button(btns, text="Open Batch Rename",
                       command=lambda: self.app.notebook.select(self.app.batch_frame)).pack(side="left", padx=8)
        if hasattr(self.app, "document_frame"):
            ttk.Button(btns, text="Open Document Tools",
                       command=lambda: self.app.notebook.select(self.app.document_frame)).pack(side="left", padx=8)

        # ALT FOOTER (daima görünür)
        footer = tk.Frame(container, bg=self.app.frame_bg)
        footer.pack(side="bottom", fill="x", pady=(6, 6))

        link = tk.Label(
            footer,
            text="www.zaferakkan.com",
            fg=self.app.accent,
            bg=self.app.frame_bg,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )
        link.pack()  # ortalanır
        link.bind("<Button-1>", lambda _e: webbrowser.open("https://www.zaferakkan.com", new=2))
        link.bind("<Enter>", lambda _e, w=link: w.config(fg="white"))
        link.bind("<Leave>", lambda _e, w=link: w.config(fg=self.app.accent))

    def _build_text_logo(self, parent):
        block = tk.Frame(parent, bg=self.app.accent, bd=0, relief="flat")
        block.pack(pady=(10, 10))
        tk.Label(block, text="BAMBAM", bg=self.app.accent, fg="#ffffff",
                 font=("Segoe UI", 20, "bold"), padx=40, pady=20).pack()
