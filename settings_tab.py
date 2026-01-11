import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading

import localization as i18n
import update_checker
from landing_tab import VERSION


class SettingsTab:
    def __init__(self, app, parent):
        self.app = app
        self.root = app.root
        self.parent = parent

        self.auto_open_var = tk.BooleanVar(value=False)

        self._build_ui()

    # -------------- UI --------------
    def _build_ui(self):
        main = ttk.Frame(self.parent)
        main.pack(fill="both", expand=True, padx=12, pady=12)

        self.lbl_title = ttk.Label(main, text=i18n.t("settings.title"), font=("Segoe UI", 12, "bold"))
        self.lbl_title.pack(anchor="w", pady=(0, 10))

        self.behavior_frame = ttk.LabelFrame(main, text=i18n.t("settings.section.behavior"))
        self.behavior_frame.pack(fill="x")

        self.chk_auto_open = ttk.Checkbutton(
            self.behavior_frame,
            text=i18n.t("settings.auto_open"),
            variable=self.auto_open_var,
        )
        self.chk_auto_open.pack(anchor="w", padx=8, pady=8)

        self.lbl_hint = ttk.Label(
            self.behavior_frame,
            text=i18n.t("settings.auto_open.hint"),
            wraplength=480,
            justify="left",
        )
        self.lbl_hint.pack(anchor="w", padx=8, pady=(0, 8))

        # Updates section
        self.updates_frame = ttk.LabelFrame(main, text=i18n.t("settings.btn.check_updates"))
        self.updates_frame.pack(fill="x", pady=(10, 0))

        # Current version
        version_row = ttk.Frame(self.updates_frame)
        version_row.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(version_row, text=i18n.t("settings.current_version")).pack(side="left")
        ttk.Label(version_row, text=VERSION, font=("", 9, "bold")).pack(side="left", padx=(5, 0))

        # Check for updates button and status label on same row
        btn_row = ttk.Frame(self.updates_frame)
        btn_row.pack(fill="x", padx=8, pady=(4, 8))
        self.btn_check_updates = ttk.Button(btn_row, text=i18n.t("settings.btn.check_updates"), 
                                           command=self._check_for_updates)
        self.btn_check_updates.pack(side="left")

        # Status label next to button
        self.lbl_update_status = ttk.Label(btn_row, text="", wraplength=400, justify="left")
        self.lbl_update_status.pack(side="left", padx=(10, 0))

        # Download button (hidden by default)
        self.btn_download = ttk.Button(self.updates_frame, text=i18n.t("settings.btn.download_update"), 
                                      command=self._open_download_page)
        self.download_url = None

    # -------------- Helpers --------------
    def should_auto_open(self) -> bool:
        return bool(self.auto_open_var.get())

    def _check_for_updates(self):
        """Check for updates from GitHub"""
        self.btn_check_updates.config(state="disabled")
        self.lbl_update_status.config(text=i18n.t("settings.checking_updates"), foreground=self.app.fg)
        self.btn_download.pack_forget()
        
        def on_result(latest_version, download_url, error):
            self.root.after(0, lambda: self._handle_update_result(latest_version, download_url, error))
        
        update_checker.get_latest_version(on_result)
    
    def _handle_update_result(self, latest_version, download_url, error):
        """Handle the result of update check"""
        self.btn_check_updates.config(state="normal")
        
        if error:
            self.lbl_update_status.config(
                text=i18n.t("settings.update_check_failed", error=error),
                foreground="#ff6b6b"
            )
            return
        
        if not latest_version:
            self.lbl_update_status.config(
                text=i18n.t("settings.update_check_failed", error="No version info"),
                foreground="#ff6b6b"
            )
            return
        
        comparison = update_checker.compare_versions(VERSION, latest_version)
        
        if comparison == 'newer':
            # New version available
            self.lbl_update_status.config(
                text=i18n.t("settings.update_available", version=latest_version),
                foreground="#7CFC00"
            )
            self.download_url = download_url
            self.btn_download.pack(anchor="w", padx=8, pady=(4, 8))
        elif comparison == 'same':
            # Up to date
            self.lbl_update_status.config(
                text=i18n.t("settings.up_to_date"),
                foreground="#7CFC00"
            )
        else:
            # Current version is newer (dev version)
            self.lbl_update_status.config(
                text=i18n.t("settings.dev_version", current=VERSION, latest=latest_version),
                foreground=self.app.fg
            )
    
    def _open_download_page(self):
        """Open the download page in browser"""
        if self.download_url:
            try:
                webbrowser.open(self.download_url)
            except Exception:
                pass

    def refresh_language(self):
        self.lbl_title.config(text=i18n.t("settings.title"))
        self.chk_auto_open.config(text=i18n.t("settings.auto_open"))
        if hasattr(self, "behavior_frame"):
            self.behavior_frame.config(text=i18n.t("settings.section.behavior"))
        self.lbl_hint.config(text=i18n.t("settings.auto_open.hint"))
        if hasattr(self, "updates_frame"):
            self.updates_frame.config(text=i18n.t("settings.section.updates"))
        if hasattr(self, "btn_check_updates"):
            self.btn_check_updates.config(text=i18n.t("settings.btn.check_updates"))
        if hasattr(self, "btn_download"):
            self.btn_download.config(text=i18n.t("settings.btn.download_update"))
