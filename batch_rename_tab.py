import os
import shutil
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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

        ttk.Label(main, text="Batch Rename", font=("Segoe UI",12,"bold")).pack(pady=(0,8))

        lf=ttk.LabelFrame(main, text="1) Select Files"); lf.pack(fill="x", **padding)
        ttk.Button(lf, text="Browse Files...", command=self._select_files).pack(side="left", padx=(5,10), pady=5)
        self.lbl_count=ttk.Label(lf, text="Selected files: 0"); self.lbl_count.pack(side="left", pady=5)
        ttk.Button(lf, text="Clear Selected", command=self._clear_selected).pack(side="right", padx=5)

        dest=ttk.LabelFrame(main, text="2) Destination"); dest.pack(fill="x", **padding)
        ttk.Checkbutton(dest, text="Rename in place", variable=self.rename_in_place,
                        command=self._toggle_dest).pack(side="left", padx=6, pady=6)
        self.btn_out=ttk.Button(dest, text="Output Folder...", command=self._select_output)
        self.btn_out.pack(side="left", padx=6, pady=5)
        self.lbl_out=ttk.Label(dest, text="Not selected"); self.lbl_out.configure(foreground="#c7b2ff")
        self.lbl_out.pack(side="left", padx=10)

        pat=ttk.LabelFrame(main, text="3) Pattern"); pat.pack(fill="x", **padding)
        ttk.Label(pat, text="Pattern:").pack(side="left", padx=(6,6))
        self.ent_pat=tk.Entry(pat, textvariable=self.pattern, width=36,
                              bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat")
        self.ent_pat.pack(side="left", padx=(0,8))
        ttk.Label(pat, text="Start #:").pack(side="left")
        tk.Entry(pat, textvariable=self.start_index, width=6,
                 bg=self.app.entry_bg, fg=self.app.fg, insertbackground=self.app.fg, relief="flat").pack(side="left", padx=(4,6))
        ttk.Label(pat, text="Placeholders: {name}, {ext}, {index}, {date}").pack(side="left", padx=(12,0))

        prev=ttk.LabelFrame(main, text="Preview"); prev.pack(fill="both", expand=True, **padding)
        self.tree=ttk.Treeview(prev, columns=("new"), show="headings", height=10)
        self.tree.heading("new", text="New Name")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        act=ttk.Frame(main); act.pack(pady=10)
        ttk.Button(act, text="Refresh Preview", command=self._refresh_preview).pack(side="left", padx=6)
        ttk.Button(act, text="Apply Rename", command=self._apply).pack(side="left", padx=6)

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
            self.lbl_count.config(text=f"Selected files: {len(self.files)}")
            self._refresh_preview()

    def _select_files(self):
        paths=filedialog.askopenfilenames(title="Select files")
        if paths:
            self.files.extend(list(paths))
            self.files=list(dict.fromkeys(self.files))
            self.lbl_count.config(text=f"Selected files: {len(self.files)}")
            self._refresh_preview()

    def _clear_selected(self):
        self.files=[]; self.lbl_count.config(text="Selected files: 0")
        for i in self.tree.get_children(): self.tree.delete(i)

    def _select_output(self):
        d=filedialog.askdirectory(title="Select output folder")
        if d:
            self.output_dir=d; self.lbl_out.config(text=d, foreground=self.app.fg)

    def _toggle_dest(self):
        state="disabled" if self.rename_in_place.get() else "normal"
        self.btn_out.configure(state=state)
        if self.rename_in_place.get():
            self.lbl_out.config(text="(in-place rename)", foreground=self.app.fg)

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
            messagebox.showwarning("Warning","No files selected."); return
        if not self.rename_in_place.get() and not self.output_dir:
            messagebox.showwarning("Warning","Please select an output folder or enable in-place rename."); return

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
                messagebox.showwarning("Error", f"Failed: {os.path.basename(p)}\n{e}")

        messagebox.showinfo("Done","Batch rename finished.")
        self._refresh_preview()
