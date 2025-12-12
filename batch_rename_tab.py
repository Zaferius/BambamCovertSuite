import os
import shutil
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import localization as i18n

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None

class BatchRenameTab:
    def __init__(self, app, parent):
        self.app = app
        self.root = app.root
        self.parent = parent

        self.files=[]
        self.pattern=tk.StringVar(value="{name}_{index}")
        self.rename_in_place=tk.BooleanVar(value=False)
        self.output_dir=""
        self.start_index=tk.IntVar(value=1)

        self._build_ui()

    def _build_ui(self):
        padding={"padx":10,"pady":5}
        main=ttk.Frame(self.parent); main.pack(fill="both", expand=True, padx=8, pady=8)

        self.lbl_title = ttk.Label(main, text=i18n.t("rename.title"), font=("Segoe UI",12,"bold"))
        self.lbl_title.pack(pady=(0,8))

        self.lf_select=ttk.LabelFrame(main, text=i18n.t("rename.section.select")); lf=self.lf_select; lf.pack(fill="x", **padding)
        self.btn_browse = ttk.Button(lf, text=i18n.t("rename.btn.browse_files"), command=self._select_files)
        self.btn_browse.pack(side="left", padx=(5,10), pady=5)
        self.lbl_count=ttk.Label(lf, text=i18n.t("rename.files.count", file_count=0)); self.lbl_count.pack(side="left", pady=5)
        self.btn_clear = ttk.Button(lf, text=i18n.t("rename.btn.clear_selected"), command=self._clear_selected)
        self.btn_clear.pack(side="right", padx=5)

        self.lf_dest=ttk.LabelFrame(main, text=i18n.t("rename.section.dest")); dest=self.lf_dest; dest.pack(fill="x", **padding)
        ttk.Checkbutton(dest, text=i18n.t("rename.dest.in_place"), variable=self.rename_in_place,
                        command=self._toggle_dest).pack(side="left", padx=6, pady=6)
        self.btn_out=ttk.Button(dest, text=i18n.t("rename.dest.btn_output"), command=self._select_output)
        self.btn_out.pack(side="left", padx=6, pady=5)
        self.lbl_out=ttk.Label(dest, text=i18n.t("rename.dest.label.not_selected")); self.lbl_out.configure(foreground="#c7b2ff")
        self.lbl_out.pack(side="left", padx=10)
        self.btn_clear_output = ttk.Button(dest, text=i18n.t("rename.dest.btn_clear_output"), command=self._clear_output)
        self.btn_clear_output.pack(side="right", padx=5)

        self.lf_pattern=ttk.LabelFrame(main, text=i18n.t("rename.section.pattern")); pat=self.lf_pattern; pat.pack(fill="x", **padding)
        self.lbl_pattern = ttk.Label(pat, text=i18n.t("rename.pattern.label")); self.lbl_pattern.pack(side="left", padx=(6,6))
        self.ent_pat=tk.Entry(pat, textvariable=self.pattern, width=36,
                              bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat")
        self.ent_pat.pack(side="left", padx=(0,8))
        self.lbl_start = ttk.Label(pat, text=i18n.t("rename.pattern.start_index")); self.lbl_start.pack(side="left")
        tk.Entry(pat, textvariable=self.start_index, width=6,
                 bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat").pack(side="left", padx=(4,6))
        self.lbl_hint = ttk.Label(pat, text=i18n.t("rename.pattern.hint")); self.lbl_hint.pack(side="left", padx=(12,0))

        self.lf_preview=ttk.LabelFrame(main, text=i18n.t("rename.section.preview")); prev=self.lf_preview; prev.pack(fill="both", expand=True, **padding)
        self.tree=ttk.Treeview(prev, columns=("new"), show="headings", height=10)
        self.tree.heading("new", text=i18n.t("rename.preview.column_new"))
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        act=ttk.Frame(main); act.pack(pady=10)
        self.btn_refresh = ttk.Button(act, text=i18n.t("rename.actions.btn.refresh"), command=self._refresh_preview)
        self.btn_refresh.pack(side="left", padx=6)
        self.btn_apply = ttk.Button(act, text=i18n.t("rename.actions.btn.apply"), command=self._apply)
        self.btn_apply.pack(side="left", padx=6)

        if DND_FILES:
            try:
                main.drop_target_register(DND_FILES)
                main.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

        self._toggle_dest()

    # --- interactions ---
    def _on_drop(self, event):
        paths=self.root.splitlist(event.data)
        added=[]
        for p in paths:
            p=p.strip()
            if os.path.isdir(p):
                for n in os.listdir(p):
                    fp=os.path.join(p,n)
                    if os.path.isfile(fp): added.append(fp)
            elif os.path.isfile(p):
                added.append(p)
        if added:
            self.files.extend(added)
            self.files=list(dict.fromkeys(self.files))
            self.lbl_count.config(text=i18n.t("rename.files.count", file_count=len(self.files)))
            self._refresh_preview()

    def _select_files(self):
        paths=filedialog.askopenfilenames(title=i18n.t("rename.section.select"))
        if paths:
            self.files.extend(list(paths))
            self.files=list(dict.fromkeys(self.files))
            self.lbl_count.config(text=i18n.t("rename.files.count", file_count=len(self.files)))
            self._refresh_preview()

    def _clear_selected(self):
        self.files=[]; self.lbl_count.config(text=i18n.t("rename.files.count", file_count=0))
        for i in self.tree.get_children(): self.tree.delete(i)

    def _select_output(self):
        d=filedialog.askdirectory(title=i18n.t("rename.section.dest"))
        if d:
            self.output_dir=d; self.lbl_out.config(text=d, foreground=self.app.fg)

    def _clear_output(self):
        self.output_dir=""
        if self.rename_in_place.get():
            self.lbl_out.config(text=i18n.t("rename.dest.label.in_place"), foreground=self.app.fg)
        else:
            self.lbl_out.config(text=i18n.t("rename.dest.label.not_selected"), foreground="#c7b2ff")

    def _toggle_dest(self):
        state="disabled" if self.rename_in_place.get() else "normal"
        self.btn_out.configure(state=state)
        if self.rename_in_place.get():
            self.lbl_out.config(text=i18n.t("rename.dest.label.in_place"), foreground=self.app.fg)

    # --- preview & apply ---
    def _render_name(self, path, idx):
        base=os.path.splitext(os.path.basename(path))[0]
        ext=os.path.splitext(path)[1].lstrip(".")
        date=datetime.datetime.now().strftime("%Y%m%d")
        try:
            new=self.pattern.get().format(name=base, ext=ext, index=self.start_index.get()+idx-1, date=date)
        except Exception:
            new=f"{base}_{self.start_index.get()+idx-1}"
        return new, ext

    def _refresh_preview(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for idx, p in enumerate(self.files, start=1):
            new, ext = self._render_name(p, idx)
            self.tree.insert("", "end", values=(f"{new}.{ext}",))

    def _apply(self):
        if not self.files:
            messagebox.showwarning(i18n.t("rename.warning.title"),i18n.t("rename.warning.no_files")); return
        if not self.rename_in_place.get() and not self.output_dir:
            messagebox.showwarning(i18n.t("rename.warning.title"),i18n.t("rename.warning.no_output")); return

        used=set()
        for idx, p in enumerate(self.files, start=1):
            new, ext = self._render_name(p, idx)
            target_dir = os.path.dirname(p) if self.rename_in_place.get() else self.output_dir
            os.makedirs(target_dir, exist_ok=True)
            target=os.path.join(target_dir, f"{new}.{ext}")

            # name clash çöz
            base, e=os.path.splitext(target); c=1
            while target.lower() in used or os.path.exists(target):
                target=f"{base}_{c}{e}"; c+=1
            used.add(target.lower())

            try:
                if self.rename_in_place.get():
                    os.rename(p, target)
                else:
                    shutil.copy2(p, target)
            except Exception as e:
                messagebox.showwarning(i18n.t("rename.error.title"), i18n.t("rename.error.message", name=os.path.basename(p), error=e))

        messagebox.showinfo(i18n.t("rename.done.title"),i18n.t("rename.done.message"))
        self._refresh_preview()

    # ------------- Localization refresh -------------
    def refresh_language(self):
        self.lbl_title.config(text=i18n.t("rename.title"))
        self.lf_select.config(text=i18n.t("rename.section.select"))
        self.btn_browse.config(text=i18n.t("rename.btn.browse_files"))
        self.btn_clear.config(text=i18n.t("rename.btn.clear_selected"))
        self.lbl_count.config(text=i18n.t("rename.files.count", file_count=len(self.files)))

        self.lf_dest.config(text=i18n.t("rename.section.dest"))
        self.btn_out.config(text=i18n.t("rename.dest.btn_output"))
        if not self.output_dir:
            if self.rename_in_place.get():
                self.lbl_out.config(text=i18n.t("rename.dest.label.in_place"))
            else:
                self.lbl_out.config(text=i18n.t("rename.dest.label.not_selected"))
        self.btn_clear_output.config(text=i18n.t("rename.dest.btn_clear_output"))

        self.lf_pattern.config(text=i18n.t("rename.section.pattern"))
        self.lbl_pattern.config(text=i18n.t("rename.pattern.label"))
        self.lbl_start.config(text=i18n.t("rename.pattern.start_index"))
        self.lbl_hint.config(text=i18n.t("rename.pattern.hint"))

        self.lf_preview.config(text=i18n.t("rename.section.preview"))
        self.tree.heading("new", text=i18n.t("rename.preview.column_new"))

        self.btn_refresh.config(text=i18n.t("rename.actions.btn.refresh"))
        self.btn_apply.config(text=i18n.t("rename.actions.btn.apply"))
