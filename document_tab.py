# document_tab.py

import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Drag & drop
try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

# Optional PDF merge support
try:
    from PyPDF2 import PdfMerger
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

DOC_INPUT_EXTS = [
    ".doc", ".docx", ".odt", ".rtf", ".txt",
    ".xls", ".xlsx", ".ppt", ".pptx",
    ".html", ".htm",
]

DOCUMENT_TARGET_FORMATS = ["PDF", "DOCX", "ODT", "TXT"]

class DocumentTab:
    def __init__(self, app, parent):
        self.app = app
        self.root = app.root
        self.parent = parent

        self.file_paths = []
        self.output_dir = ""
        self.target_format = tk.StringVar(value="PDF")

        self.drop_canvas = None

        self.engine_type = "none"
        self.engine_name = "None"
        self._detect_engine()

        # Advanced settings
        self.advanced_visible = tk.BooleanVar(value=False)
        self.open_folder_when_done = tk.BooleanVar(value=False)
        self.preserve_timestamps = tk.BooleanVar(value=False)
        self.delete_originals = tk.BooleanVar(value=False)
        self.merge_pdfs = tk.BooleanVar(value=False)

        self.adv_content = None

        self._build_ui()
        self._setup_drag_and_drop()
        self._update_controls_state()

    # ---------------- Engine detection ----------------
    def _detect_engine(self):
        # Try Word (Windows)
        try:
            import win32com.client  # type: ignore
            try:
                word = win32com.client.Dispatch("Word.Application")
                word.Quit()
                self.engine_type = "word"
                self.engine_name = "Microsoft Word (COM)"
                return
            except Exception:
                pass
        except ImportError:
            pass

        # Try LibreOffice
        try:
            result = subprocess.run(
                ["soffice", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode == 0:
                self.engine_type = "libreoffice"
                self.engine_name = "LibreOffice (soffice)"
                return
        except FileNotFoundError:
            pass

        self.engine_type = "none"
        self.engine_name = "None"

    # ---------------- UI ----------------
    def _build_ui(self):
        padding = {"padx": 10, "pady": 5}

        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        header = ttk.Label(
            main_frame,
            text="Bambam Document Converter",
            font=("Segoe UI", 12, "bold"),
        )
        header.pack(pady=(0, 8))

        # Engine status
        frame_engine = ttk.LabelFrame(main_frame, text="Engine Status")
        frame_engine.pack(fill="x", **padding)

        if self.engine_type in ("word", "libreoffice"):
            txt = f"Detected engine: {self.engine_name}"
            color = "#7CFC00"
        else:
            txt = (
                "No office engine detected.\n"
                "Install LibreOffice (free) or Microsoft Word and restart the app."
            )
            color = "#ff6b6b"

        self.lbl_engine = ttk.Label(frame_engine, text=txt, justify="left")
        self.lbl_engine.pack(anchor="w", padx=8, pady=5)
        self.lbl_engine.configure(foreground=color)

        # 1) Select documents
        frame_files = ttk.LabelFrame(main_frame, text="1) Select Documents")
        frame_files.pack(fill="x", **padding)

        self.drop_canvas = tk.Canvas(
            frame_files,
            bg=self.app.frame_bg,
            highlightthickness=0,
            height=90,
        )
        self.drop_canvas.pack(fill="x", padx=6, pady=6)
        self.drop_canvas.bind("<Configure>", self._draw_drop_zone_border)

        inner = ttk.Frame(self.drop_canvas)
        self.drop_canvas.create_window(10, 10, window=inner, anchor="nw")

        top_row = ttk.Frame(inner)
        top_row.pack(fill="x", pady=(0, 2))

        self.btn_select = ttk.Button(top_row, text="Browse Documents...", command=self.select_files)
        self.btn_select.pack(side="left", padx=(0, 10), pady=2)

        self.lbl_file_count = ttk.Label(top_row, text="Selected files: 0")
        self.lbl_file_count.pack(side="left", pady=2)

        self.lbl_hint = ttk.Label(
            inner,
            text="You can also drag & drop documents onto this area.",
            wraplength=470,
            justify="left",
        )
        self.lbl_hint.pack(anchor="w", pady=(4, 0))

        # 2) Output folder (+ clear)
        frame_output = ttk.LabelFrame(main_frame, text="2) Select Output Folder")
        frame_output.pack(fill="x", **padding)

        self.btn_output = ttk.Button(frame_output, text="Browse Folder...", command=self.select_output_dir)
        self.btn_output.pack(side="left", padx=5, pady=5)

        self.lbl_output_dir = ttk.Label(frame_output, text="Not selected")
        self.lbl_output_dir.configure(foreground="#c7b2ff")
        self.lbl_output_dir.pack(side="left", padx=10)

        btn_clear_out = ttk.Button(frame_output, text="Clear Output Folder", command=self.clear_output_folder_contents)
        btn_clear_out.pack(side="right", padx=5)
        btn_clear_sel = ttk.Button(frame_output, text="Clear Selected", command=self.clear_selected_files)
        btn_clear_sel.pack(side="right", padx=5)

        # 3) Target format
        frame_format = ttk.LabelFrame(main_frame, text="3) Target Format")
        frame_format.pack(fill="x", **padding)

        ttk.Label(frame_format, text="Format:").pack(side="left", padx=5, pady=5)

        self.format_menu = tk.OptionMenu(
            frame_format,
            self.target_format,
            *DOCUMENT_TARGET_FORMATS,
        )
        self.format_menu.pack(side="left", padx=5, pady=5)
        self.format_menu.config(
            bg=self.app.entry_bg,
            fg=self.app.fg,
            activebackground=self.app.button_hover,
            activeforeground=self.app.fg,
            highlightthickness=1,
            highlightbackground=self.app.border,
            relief="flat",
            font=self.app.title_font,
        )
        menu = self.format_menu["menu"]
        menu.config(
            bg=self.app.entry_bg,
            fg=self.app.fg,
            activebackground=self.app.button_hover,
            activeforeground=self.app.fg,
            font=self.app.title_font,
        )

        # 4) Advanced (collapsible)
        frame_adv = ttk.LabelFrame(main_frame, text="4) Advanced Document Tools (optional)")
        frame_adv.pack(fill="x", **padding)

        toggle_chk = ttk.Checkbutton(
            frame_adv,
            text="Show advanced settings",
            variable=self.advanced_visible,
            command=self.on_toggle_advanced,
        )
        toggle_chk.pack(anchor="w", padx=5, pady=(3, 3))

        self.adv_content = ttk.Frame(frame_adv)

        chk_open = ttk.Checkbutton(
            self.adv_content,
            text="Open output folder when finished",
            variable=self.open_folder_when_done,
        )
        chk_open.pack(anchor="w", padx=5, pady=(3, 2))

        chk_preserve = ttk.Checkbutton(
            self.adv_content,
            text="Preserve original timestamps on converted files",
            variable=self.preserve_timestamps,
        )
        chk_preserve.pack(anchor="w", padx=5, pady=(0, 2))

        chk_delete = ttk.Checkbutton(
            self.adv_content,
            text="Delete original files after successful conversion (dangerous!)",
            variable=self.delete_originals,
        )
        chk_delete.pack(anchor="w", padx=5, pady=(0, 2))

        chk_merge = ttk.Checkbutton(
            self.adv_content,
            text="Merge all converted PDFs into a single PDF (PDF only, requires PyPDF2)",
            variable=self.merge_pdfs,
        )
        chk_merge.pack(anchor="w", padx=5, pady=(0, 2))

        adv_hint = ttk.Label(
            self.adv_content,
            text="Note: Merge works only when target format is PDF. If PyPDF2 is missing, merge will be skipped.",
        )
        adv_hint.pack(anchor="w", padx=5, pady=(2, 3))

        self.on_toggle_advanced()

        # 5) Progress
        frame_progress = ttk.LabelFrame(main_frame, text="5) Progress")
        frame_progress.pack(fill="x", **padding)

        self.progress = ttk.Progressbar(frame_progress, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        self.lbl_progress = ttk.Label(frame_progress, text="0 / 0")
        self.lbl_progress.pack(pady=2)

        # 6) Start button
        frame_actions = ttk.Frame(main_frame)
        frame_actions.pack(fill="x", pady=8)

        self.btn_convert = ttk.Button(frame_actions, text="Start Conversion", command=self.start_conversion)
        self.btn_convert.pack(pady=4)

    # ---------------- advanced collapse ----------------
    def on_toggle_advanced(self):
        if self.advanced_visible.get():
            self.adv_content.pack(fill="x", padx=0, pady=(0, 5))
        else:
            self.adv_content.pack_forget()

    # ---------------- controls state ----------------
    def _update_controls_state(self):
        has_engine = self.engine_type in ("word", "libreoffice")
        state = "normal" if has_engine else "disabled"
        self.btn_select.config(state=state)
        self.btn_output.config(state=state)
        self.format_menu.config(state=state)
        self.btn_convert.config(state=state)

    # ---------------- dashed border ----------------
    def _draw_drop_zone_border(self, event):
        if not self.drop_canvas:
            return
        self.drop_canvas.delete("border")
        margin = 4
        self.drop_canvas.create_rectangle(
            margin, margin, event.width - margin, event.height - margin,
            outline=self.app.fg, dash=(4, 3), width=1, tags="border",
        )

    # ---------------- drag & drop ----------------
    def _setup_drag_and_drop(self):
        has_engine = self.engine_type in ("word", "libreoffice")
        if DND_FILES is None or not has_engine:
            return
        try:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self.on_drop)
        except Exception:
            pass

    def on_drop(self, event):
        if self.engine_type not in ("word", "libreoffice"):
            return
        raw = event.data
        paths = self.root.splitlist(raw)

        new_files = []
        for p in paths:
            p = p.strip()
            if os.path.isdir(p):
                for name in os.listdir(p):
                    full = os.path.join(p, name)
                    if os.path.isfile(full) and self.is_document_file(full):
                        new_files.append(full)
            elif os.path.isfile(p) and self.is_document_file(p):
                new_files.append(p)

        if new_files:
            self.file_paths.extend(new_files)
            self.file_paths = list(dict.fromkeys(self.file_paths))
            self.update_file_count()

    # ---------------- helpers ----------------
    def is_document_file(self, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in DOC_INPUT_EXTS

    def update_file_count(self):
        self.lbl_file_count.config(text=f"Selected files: {len(self.file_paths)}")

    # ---------------- clear buttons ----------------
    def clear_selected_files(self):
        self.file_paths = []
        self.update_file_count()

    def clear_output_folder_contents(self):
        import shutil
        if not self.output_dir:
            messagebox.showinfo("Info", "Output folder is not selected.")
            return
        if not os.path.isdir(self.output_dir):
            messagebox.showwarning("Warning", "Output folder does not exist.")
            return
        if not messagebox.askyesno("Confirm", f"Delete ALL files in:\n{self.output_dir}?"):
            return
        deleted = 0
        for name in os.listdir(self.output_dir):
            p = os.path.join(self.output_dir, name)
            try:
                if os.path.isfile(p) or os.path.islink(p):
                    os.remove(p)
                    deleted += 1
                elif os.path.isdir(p):
                    shutil.rmtree(p)
                    deleted += 1
            except Exception:
                pass
        messagebox.showinfo("Done", f"Deleted {deleted} item(s) in output folder.")

    # ---------------- UI callbacks ----------------
    def select_files(self):
        if self.engine_type not in ("word", "libreoffice"):
            messagebox.showwarning(
                "No engine",
                "No office engine detected. Install LibreOffice or Microsoft Word and restart the app.",
            )
            return

        filetypes = [
            ("Documents", "*.doc *.docx *.odt *.rtf *.txt *.xls *.xlsx *.ppt *.pptx *.html *.htm"),
            ("Word", "*.doc *.docx"),
            ("Text", "*.txt"),
            ("Office", "*.xls *.xlsx *.ppt *.pptx"),
            ("All files", "*.*"),
        ]
        paths = filedialog.askopenfilenames(
            title="Select documents",
            filetypes=filetypes,
        )
        if paths:
            self.file_paths.extend(list(paths))
            self.file_paths = list(dict.fromkeys(self.file_paths))
            self.update_file_count()

    def select_output_dir(self):
        if self.engine_type not in ("word", "libreoffice"):
            return
        directory = filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_dir = directory
            short = directory
            if len(short) > 45:
                short = "..." + short[-45:]
            self.lbl_output_dir.config(text=short, foreground=self.app.fg)

    def start_conversion(self):
        if self.engine_type not in ("word", "libreoffice"):
            messagebox.showwarning(
                "No engine",
                "No office engine detected. Install LibreOffice or Microsoft Word and restart the app.",
            )
            return

        # Word engine ODT output'u desteklemiyor
        if self.engine_type == "word" and self.target_format.get().upper() == "ODT":
            messagebox.showwarning(
                "Not supported",
                "ODT output is not supported with Microsoft Word engine.\n"
                "Please choose PDF, DOCX or TXT as target format.",
            )
            return

        if not self.file_paths:
            messagebox.showwarning("Warning", "Please select at least one document.")
            return
        if not self.output_dir:
            messagebox.showwarning("Warning", "Please select an output folder.")
            return

        self.progress["value"] = 0
        self.lbl_progress.config(text=f"0 / {len(self.file_paths)}")
        self.btn_convert.config(state="disabled")

        t = threading.Thread(target=self.convert_documents, daemon=True)
        t.start()

    # ---------------- conversion logic ----------------
    def _get_convert_filter_libre(self):
        fmt = self.target_format.get().upper()
        if fmt == "PDF":
            return "pdf:writer_pdf_Export", "pdf"
        elif fmt == "DOCX":
            return "docx", "docx"
        elif fmt == "ODT":
            return "odt", "odt"
        elif fmt == "TXT":
            return "txt:Text", "txt"
        else:
            return "pdf:writer_pdf_Export", "pdf"

    def convert_documents(self):
        total = len(self.file_paths)
        errors = []

        open_folder = self.open_folder_when_done.get()
        preserve_ts = self.preserve_timestamps.get()
        delete_orig = self.delete_originals.get()
        do_merge = self.merge_pdfs.get() and (self.target_format.get().upper() == "PDF")

        converted_paths = []

        try:
            if self.engine_type == "libreoffice":
                convert_filter, out_ext = self._get_convert_filter_libre()
                self._convert_with_libreoffice(
                    convert_filter, out_ext, preserve_ts, delete_orig, converted_paths, errors
                )
            elif self.engine_type == "word":
                out_ext = self._get_word_output_ext()
                if out_ext is None:
                    raise RuntimeError("Unsupported format for Word engine.")
                self._convert_with_word(
                    out_ext, preserve_ts, delete_orig, converted_paths, errors
                )
            else:
                errors.append(("Engine", "No engine available."))
        finally:
            if do_merge and converted_paths:
                self._maybe_merge_pdfs(converted_paths, errors)

            self.root.after(0, self.finish_conversion, total, errors, converted_paths, open_folder)

    def _convert_with_libreoffice(self, convert_filter, out_ext, preserve_ts, delete_orig, converted_paths, errors_list):
        for idx, path in enumerate(self.file_paths, start=1):
            try:
                base_name = os.path.splitext(os.path.basename(path))[0].replace(os.sep, "_")
                out_path = os.path.join(self.output_dir, f"{base_name}.{out_ext}")
                out_path = self._avoid_overwrite(out_path)

                cmd = [
                    "soffice", "--headless", "--convert-to", convert_filter,
                    "--outdir", self.output_dir, path,
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or "soffice error")

                produced_path = os.path.join(self.output_dir, f"{os.path.splitext(os.path.basename(path))[0]}.{out_ext}")
                if not os.path.exists(produced_path) and os.path.exists(out_path):
                    produced_path = out_path

                if os.path.exists(produced_path):
                    if preserve_ts:
                        try:
                            st = os.stat(path)
                            os.utime(produced_path, (st.st_atime, st.st_mtime))
                        except Exception:
                            pass

                    converted_paths.append(produced_path)
                    if delete_orig:
                        try:
                            os.remove(path)
                        except Exception:
                            pass
                else:
                    raise RuntimeError("Output file not found after conversion.")

            except Exception as e:
                errors_list.append((path, str(e)))

            self.root.after(0, self.update_progress, idx, len(self.file_paths))

    # ----- Word conversion -----
    def _get_word_output_ext(self):
        fmt = self.target_format.get().upper()
        if fmt == "PDF":
            return "pdf"
        elif fmt == "DOCX":
            return "docx"
        elif fmt == "TXT":
            return "txt"
        else:
            return None

    def _get_word_fileformat(self):
        # 17=PDF, 16=DOCX, 2=TXT
        fmt = self.target_format.get().upper()
        return { "PDF":17, "DOCX":16, "TXT":2 }.get(fmt)

    def _convert_with_word(self, out_ext, preserve_ts, delete_orig, converted_paths, errors_list):
        try:
            import win32com.client  # type: ignore
        except ImportError:
            errors_list.append(("Word engine", "pywin32 is not installed."))
            return

        fileformat = self._get_word_fileformat()
        if fileformat is None:
            errors_list.append(("Word engine", "Unsupported target format for Word."))
            return

        word = None
        try:
            word = win32com.client.gencache.EnsureDispatch("Word.Application")
            word.Visible = False

            for idx, path in enumerate(self.file_paths, start=1):
                try:
                    ext = os.path.splitext(path)[1].lower()
                    if ext not in [".doc", ".docx", ".rtf", ".txt", ".html", ".htm"]:
                        raise RuntimeError("This file type is not supported by Word engine.")

                    doc = word.Documents.Open(path)
                    base_name = os.path.splitext(os.path.basename(path))[0].replace(os.sep, "_")
                    out_path = os.path.join(self.output_dir, f"{base_name}.{out_ext}")
                    out_path = self._avoid_overwrite(out_path)

                    doc.SaveAs(out_path, FileFormat=fileformat)
                    doc.Close(False)

                    if os.path.exists(out_path):
                        if preserve_ts:
                            try:
                                st = os.stat(path)
                                os.utime(out_path, (st.st_atime, st.st_mtime))
                            except Exception:
                                pass

                        converted_paths.append(out_path)
                        if delete_orig:
                            try:
                                os.remove(path)
                            except Exception:
                                pass
                    else:
                        raise RuntimeError("Output file not found after Word conversion.")

                except Exception as e:
                    errors_list.append((path, str(e)))

                self.root.after(0, self.update_progress, idx, len(self.file_paths))
        finally:
            if word is not None:
                try:
                    word.Quit()
                except Exception:
                    pass

    # ----- PDF merge -----
    def _maybe_merge_pdfs(self, pdf_paths, errors_list):
        if not HAS_PYPDF2:
            errors_list.append(("PDF merge", "PyPDF2 is not installed. Run 'pip install PyPDF2'."))
            return
        try:
            merger = PdfMerger()
            for p in pdf_paths:
                if os.path.exists(p):
                    merger.append(p)
            merged_path = os.path.join(self.output_dir, "merged_output.pdf")
            merged_path = self._avoid_overwrite(merged_path)
            with open(merged_path, "wb") as f:
                merger.write(f)
            merger.close()
        except Exception as e:
            errors_list.append(("PDF merge", str(e)))

    # ----- common helpers -----
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
        percent = (current / max(1, total)) * 100
        self.progress["value"] = percent
        self.lbl_progress.config(text=f"{current} / {total}")

    def finish_conversion(self, total, errors, converted_paths, open_folder):
        self.btn_convert.config(state="normal")
        if errors:
            msg = (
                "Document conversion finished with errors.\n\n"
                f"{len(errors)} out of {total} file(s) had issues.\n\n"
                f"First error:\n{errors[0][0]}\n{errors[0][1]}"
            )
            messagebox.showwarning("Completed with errors", msg)
        else:
            messagebox.showinfo("Done", f"All {total} file(s) converted successfully!")

        if open_folder and self.output_dir and os.path.isdir(self.output_dir):
            try:
                if os.name == "nt":
                    os.startfile(self.output_dir)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", self.output_dir])
                else:
                    subprocess.Popen(["xdg-open", self.output_dir])
            except Exception:
                pass
