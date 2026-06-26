#!/usr/bin/env python3
"""
Xite v0.3
Minimalist native editor for X++ (.xp)
- Dark, distraction-free UI
- File explorer
- Syntax highlighting (X++ strict)
- Run: XCOM / XITR / ITR with live output
- No web dependencies – pure Tkinter

Aagastya Verma / Atom Software
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
import os, sys, re, subprocess, threading, queue, time

# ---------- theme ----------
DARK = {
    "bg":         "#13131a",
    "bg2":        "#1a1a22",
    "bg3":        "#0f0f14",
    "sidebar":    "#111119",
    "text":       "#d8dce4",
    "muted":      "#7a8194",
    "comment":    "#5c6370",
    "keyword":    "#c678dd",
    "keyword2":   "#e06c75",
    "fn":         "#61afef",
    "string":     "#98c379",
    "number":     "#d19a66",
    "accent":     "#7c5cff",
    "accent2":    "#5b8def",
    "border":     "#222230",
    "output_bg":  "#0f0f15",
    "output_fg":  "#b8bcc8",
    "selection":  "#2a2a3a",
    "line_num":   "#4b5263",
    "line_num_bg":"#171720",
    "gutter":     "#1d1d28",
    "success":    "#4ade80",
    "error":      "#f87171",
    "warn":       "#fbbf24",
}

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = APP_DIR

# ---------- syntax ----------
XPP_KEYWORDS = r'\b(fn|end|if|elif|else|while|loop|from|to|step|in|safe|fail|return|break|continue|out|push|and|or|not|true|false|nil|len|read)\b'
XPP_DIRECTIVE = r'\bRNM\s*=\s*(?:XCOM|XITR|ITR|AI)\b|USE\s+MODEL\b'
XPP_BUILTIN = r'\b(print|input|range|len|int|float|str|abs|min|max|sum|sorted|open)\b'

def configure_ttk_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TFrame", background=DARK["bg"])
    style.configure("Sidebar.TFrame", background=DARK["sidebar"])
    style.configure("Toolbar.TFrame", background=DARK["bg2"])
    style.configure("TLabel", background=DARK["bg"], foreground=DARK["text"], font=("Segoe UI", 9))
    style.configure("Sidebar.TLabel", background=DARK["sidebar"], foreground=DARK["muted"])
    style.configure("Status.TLabel", background=DARK["bg3"], foreground=DARK["muted"], font=("Segoe UI", 8))
    style.configure("Accent.TButton",
        background=DARK["accent"], foreground="#ffffff",
        borderwidth=0, focusthickness=0, padding=6,
        font=("Segoe UI Semibold", 9)
    )
    style.map("Accent.TButton",
        background=[("active", "#8c6eff"), ("pressed", "#6a47e6")],
        foreground=[("!disabled", "#ffffff")]
    )
    style.configure("Tool.TButton",
        background=DARK["bg2"], foreground=DARK["text"],
        borderwidth=0, padding=(10,5), font=("Segoe UI", 9)
    )
    style.map("Tool.TButton",
        background=[("active", "#252538")],
        foreground=[("active", "#ffffff")]
    )
    # Treeview – file explorer
    style.configure("Treeview",
        background=DARK["sidebar"],
        foreground=DARK["text"],
        fieldbackground=DARK["sidebar"],
        borderwidth=0,
        font=("Segoe UI", 9),
        rowheight=24
    )
    style.map("Treeview",
        background=[("selected", DARK["selection"])],
        foreground=[("selected", "#ffffff")]
    )
    style.configure("Treeview.Heading", background=DARK["sidebar"], foreground=DARK["muted"], borderwidth=0)
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
    # Combobox
    style.configure("TCombobox",
        fieldbackground=DARK["bg3"],
        background=DARK["bg3"],
        foreground=DARK["text"],
        arrowcolor=DARK["muted"],
        borderwidth=0,
        padding=4
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", DARK["bg3"])],
        foreground=[("readonly", DARK["text"])]
    )
    # Panedwindow
    style.configure("TPanedwindow", background=DARK["bg"])


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.configure(
            width=52,
            background=DARK["line_num_bg"],
            highlightthickness=0,
            bd=0
        )

    def redraw(self, *args):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(
                44, y, anchor="ne",
                text=linenum,
                fill=DARK["line_num"],
                font=self.text_widget["font"]
            )
            i = self.text_widget.index(f"{i}+1line")


class CodeEditor(tk.Frame):
    def __init__(self, master, on_change=None, **kwargs):
        super().__init__(master, background=DARK["bg"], **kwargs)
        self.on_change = on_change
        self._highlight_after = None

        # font – try JetBrains Mono / Cascadia / Consolas fallback
        for fam in ("JetBrains Mono", "Cascadia Code", "Cascadia Mono", "Consolas", "Menlo", "Monaco", "Courier New"):
            try:
                test = tkfont.Font(family=fam, size=11)
                if test.actual("family") in (fam, fam.replace(" ", "")):
                    editor_font = (fam, 11)
                    break
            except Exception:
                continue
        else:
            editor_font = ("Consolas", 11)

        # line numbers
        self.linenumbers = LineNumbers(self, None, height=400)
        self.linenumbers.pack(side="left", fill="y")

        # text + scroll
        text_frame = tk.Frame(self, background=DARK["bg2"])
        text_frame.pack(side="left", fill="both", expand=True)

        self.text = tk.Text(
            text_frame,
            wrap="none",
            undo=True,
            background=DARK["bg2"],
            foreground=DARK["text"],
            insertbackground="#d8dce4",
            selectbackground=DARK["selection"],
            selectforeground="#ffffff",
            font=editor_font,
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            insertwidth=2,
            tabs="    ",
            spacing1=2,
            spacing3=2
        )
        self.linenumbers.text_widget = self.text

        y_scroll = tk.Scrollbar(text_frame, orient="vertical", command=self._on_scroll, width=12,
                                background=DARK["bg"], troughcolor=DARK["bg3"],
                                activebackground=DARK["border"], relief="flat", bd=0)
        x_scroll = tk.Scrollbar(text_frame, orient="horizontal", command=self.text.xview, width=12,
                                background=DARK["bg"], troughcolor=DARK["bg3"], relief="flat", bd=0)

        self.text.configure(yscrollcommand=lambda *a: (y_scroll.set(*a), self.linenumbers.redraw()))
        self.text.configure(xscrollcommand=x_scroll.set)

        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.text.pack(side="left", fill="both", expand=True)

        # tags – syntax
        self.text.tag_configure("keyword", foreground=DARK["keyword"])
        self.text.tag_configure("keyword2", foreground=DARK["keyword2"])
        self.text.tag_configure("builtin", foreground=DARK["fn"])
        self.text.tag_configure("string", foreground=DARK["string"])
        self.text.tag_configure("comment", foreground=DARK["comment"])
        self.text.tag_configure("number", foreground=DARK["number"])
        self.text.tag_configure("directive", foreground=DARK["accent2"])
        self.text.tag_configure("function", foreground=DARK["fn"])
        self.text.tag_configure("found", background="#3a2a5a", foreground="#ffffff")

        # events
        self.text.bind("<KeyRelease>", self._on_key)
        self.text.bind("<ButtonRelease>", lambda e: self.linenumbers.redraw())
        self.text.bind("<MouseWheel>", lambda e: self.after_idle(self.linenumbers.redraw))
        self.text.bind("<Configure>", lambda e: self.linenumbers.redraw())
        self.text.bind("<<Change>>", lambda e: self.linenumbers.redraw())
        # bracket matching / auto indent
        self.text.bind("<Return>", self._auto_indent)
        self.text.bind("<Tab>", self._tab)
        self.text.bind("<Shift-Tab>", self._unindent)
        self.text.bind("<Control-f>", lambda e: "break")  # handled at root

        self._highlight()

    def _on_scroll(self, *args):
        self.text.yview(*args)
        self.linenumbers.redraw()

    def _on_key(self, event=None):
        self.linenumbers.redraw()
        if self.on_change:
            self.on_change()
        # debounce highlight
        if self._highlight_after:
            self.after_cancel(self._highlight_after)
        self._highlight_after = self.after(140, self._highlight)

    def _auto_indent(self, event):
        # get current line indent
        idx = self.text.index("insert")
        line_start = f"{idx.split('.')[0]}.0"
        line_text = self.text.get(line_start, idx)
        indent = re.match(r'^(\s*)', line_text).group(1)
        # increase after : 
        if line_text.rstrip().endswith(":"):
            indent += "    "
        self.text.insert("insert", "\n" + indent)
        return "break"

    def _tab(self, event):
        # indent selection or insert 4 spaces
        try:
            start = self.text.index("sel.first linestart")
            end = self.text.index("sel.last lineend")
            # indent each line
            data = self.text.get(start, end).split("\n")
            new = "\n".join("    " + l for l in data)
            self.text.delete(start, end)
            self.text.insert(start, new)
            return "break"
        except tk.TclError:
            self.text.insert("insert", "    ")
            return "break"

    def _unindent(self, event):
        try:
            start = self.text.index("sel.first linestart")
            end = self.text.index("sel.last lineend")
            data = self.text.get(start, end).split("\n")
            new_lines = []
            for l in data:
                if l.startswith("    "): new_lines.append(l[4:])
                elif l.startswith("\t"): new_lines.append(l[1:])
                else: new_lines.append(l.lstrip())
            self.text.delete(start, end)
            self.text.insert(start, "\n".join(new_lines))
            return "break"
        except tk.TclError:
            # single line unindent
            line_start = self.text.index("insert linestart")
            line = self.text.get(line_start, f"{line_start} lineend")
            if line.startswith("    "):
                self.text.delete(line_start, f"{line_start}+4c")
            return "break"

    def get_text(self):
        return self.text.get("1.0", "end-1c")

    def set_text(self, txt):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", txt)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self._highlight()
        self.linenumbers.redraw()

    def _highlight(self):
        content = self.text.get("1.0", "end-1c")
        # clear
        for tag in ("keyword","keyword2","builtin","string","comment","number","directive","function"):
            self.text.tag_remove(tag, "1.0", "end")
        # strings
        for m in re.finditer(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', content):
            s,e = m.span()
            self.text.tag_add("string", f"1.0+{s}c", f"1.0+{e}c")
        # comments – must be after strings to avoid # inside strings
        # remove strings temporarily? simpler: tag comments then re-apply strings over – already did strings first, so do comments with care
        # actually easier: do comments first then strings overwrite – we did strings first, so redo:
        self.text.tag_remove("comment", "1.0", "end")
        for m in re.finditer(r'#[^\n]*', content):
            s,e = m.span()
            # check if inside string tag – crude: skip if string tag already covers start
            overlapping = self.text.tag_ranges("string")
            inside = False
            for i in range(0, len(overlapping), 2):
                if self.text.compare(f"1.0+{s}c", ">=", overlapping[i]) and self.text.compare(f"1.0+{s}c", "<", overlapping[i+1]):
                    inside = True; break
            if not inside:
                self.text.tag_add("comment", f"1.0+{s}c", f"1.0+{e}c")
        # re-apply strings to win over comments
        for m in re.finditer(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', content):
            s,e = m.span()
            self.text.tag_add("string", f"1.0+{s}c", f"1.0+{e}c")

        # directives
        for m in re.finditer(XPP_DIRECTIVE, content):
            s,e = m.span()
            self.text.tag_add("directive", f"1.0+{s}c", f"1.0+{e}c")
        # keywords
        for m in re.finditer(XPP_KEYWORDS, content):
            s,e = m.span()
            self.text.tag_add("keyword", f"1.0+{s}c", f"1.0+{e}c")
        # builtins
        for m in re.finditer(XPP_BUILTIN, content):
            s,e = m.span()
            self.text.tag_add("builtin", f"1.0+{s}c", f"1.0+{e}c")
        # numbers
        for m in re.finditer(r'\b\d+(?:\.\d+)?\b', content):
            s,e = m.span()
            self.text.tag_add("number", f"1.0+{s}c", f"1.0+{e}c")
        # function defs: fn name
        for m in re.finditer(r'\bfn\s+([A-Za-z_]\w*)', content):
            s,e = m.span(1)
            self.text.tag_add("function", f"1.0+{s}c", f"1.0+{e}c")
        # def name(  (generated python preview)
        for m in re.finditer(r'\bdef\s+([A-Za-z_]\w*)', content):
            s,e = m.span(1)
            self.text.tag_add("function", f"1.0+{s}c", f"1.0+{e}c")


class FileTree(ttk.Frame):
    def __init__(self, master, on_open=None):
        super().__init__(master, style="Sidebar.TFrame")
        self.on_open = on_open
        self.root_path = None

        hdr = ttk.Frame(self, style="Sidebar.TFrame")
        hdr.pack(fill="x", padx=10, pady=(12,6))
        ttk.Label(hdr, text="EXPLORER", style="Sidebar.TLabel", font=("Segoe UI Semibold", 8)).pack(side="left")
        
        self.tree = ttk.Treeview(self, show="tree", selectmode="browse")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree.bind("<Double-1>", self._dbl)
        self.tree.bind("<<TreeviewOpen>>", self._expand)

        # scrollbar thin
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        # vsb.pack(side="right", fill="y")  # hidden for minimalism

    def set_root(self, path):
        self.root_path = os.path.abspath(path)
        self.tree.delete(*self.tree.get_children())
        root_id = self.tree.insert("", "end", text=os.path.basename(path) or path,
                                   values=[self.root_path], open=True)
        self._populate(root_id, self.root_path)

    def _populate(self, parent_id, folder):
        try:
            entries = sorted(os.scandir(folder), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        # clear existing children to avoid duplicates
        for ch in self.tree.get_children(parent_id):
            self.tree.delete(ch)
        for e in entries:
            if e.name.startswith(".") and e.name not in (".gitignore",): 
                # hide dotfiles except useful ones
                if e.name in (".git", "__pycache__", ".xpp_cache", ".x_cache", ".venv", "node_modules"):
                    continue
            node = self.tree.insert(parent_id, "end", text=e.name,
                                    values=[e.path],
                                    open=False)
            # add dummy child for folders to show expand arrow
            if e.is_dir():
                self.tree.insert(node, "end", text="…")
    
    def _expand(self, event):
        item = self.tree.focus()
        if not item: return
        vals = self.tree.item(item, "values")
        if not vals: return
        path = vals[0]
        if os.path.isdir(path):
            # if first child is dummy
            children = self.tree.get_children(item)
            if children and self.tree.item(children[0], "text") == "…":
                self._populate(item, path)

    def _dbl(self, event):
        item = self.tree.focus()
        if not item: return
        vals = self.tree.item(item, "values")
        if not vals: return
        path = vals[0]
        if os.path.isfile(path) and self.on_open:
            self.on_open(path)


class XiteIDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Xite • v0.3")
        self.geometry("1280x800")
        self.configure(bg=DARK["bg"])
        try:
            self.iconphoto(False, tk.PhotoImage(width=1, height=1))
        except Exception:
            pass

        configure_ttk_style(self)

        self.current_file = None
        self.folder_root = os.path.join(REPO_ROOT, "examples") if os.path.isdir(os.path.join(REPO_ROOT, "examples")) else REPO_ROOT
        self.dirty = False
        self.proc = None

        self._build_ui()
        self._bind_keys()

        # auto open test.xp or hello.xp
        for cand in [
            os.path.join(REPO_ROOT, "test.xp"),
            os.path.join(REPO_ROOT, "examples", "hello.xp"),
        ]:
            if os.path.exists(cand):
                self.open_file_path(cand)
                break

        self._update_title()
        self.after(120, self._tick)

    # ---------- UI ----------
    def _build_ui(self):
        # toolbar
        tb = ttk.Frame(self, style="Toolbar.TFrame", height=44)
        tb.pack(side="top", fill="x")
        tb.pack_propagate(False)

        # left side: app logo
        logo = tk.Label(tb, text="  Xite", bg=DARK["bg2"], fg="#ffffff",
                        font=("Segoe UI Semibold", 13))
        logo.pack(side="left", padx=(14,18))

        def tbtn(parent, text, cmd, accent=False):
            b = ttk.Button(parent, text=text, command=cmd,
                           style="Accent.TButton" if accent else "Tool.TButton",
                           takefocus=False, cursor="hand2")
            b.pack(side="left", padx=2, pady=8)
            return b

        tbtn(tb, "Open Folder", self.open_folder)
        tbtn(tb, "Save  ⌘S", self.save_file)
        ttk.Frame(tb, style="Toolbar.TFrame", width=14).pack(side="left")

        tbtn(tb, "▶ Run", self.run_file, accent=True)

        # mode selector
        mode_frame = tk.Frame(tb, bg=DARK["bg2"])
        mode_frame.pack(side="left", padx=14)
        tk.Label(mode_frame, text="mode", bg=DARK["bg2"], fg=DARK["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")
        self.mode_var = tk.StringVar(value="XITR")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var,
                                  values=["XITR","XCOM","ITR","AI"],
                                  width=6, state="readonly", font=("Segoe UI", 9))
        mode_combo.pack()

        # right side buttons
        tbtn(tb, "⟲", self.run_file).pack(side="right", padx=8)
        tbtn(tb, "⛶", self.toggle_output).pack(side="right")

        # main paned
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True)

        # sidebar
        sidebar = ttk.Frame(main_pane, style="Sidebar.TFrame", width=260)
        main_pane.add(sidebar, weight=0)
        self.file_tree = FileTree(sidebar, on_open=self.open_file_path)
        self.file_tree.pack(fill="both", expand=True)
        if os.path.isdir(self.folder_root):
            self.file_tree.set_root(self.folder_root)

        # right side vertical
        right = ttk.Frame(main_pane)
        main_pane.add(right, weight=1)

        v_pane = ttk.PanedWindow(right, orient=tk.VERTICAL)
        v_pane.pack(fill="both", expand=True)

        # editor
        editor_wrap = ttk.Frame(v_pane)
        v_pane.add(editor_wrap, weight=3)
        self.editor = CodeEditor(editor_wrap, on_change=self._on_edit)
        self.editor.pack(fill="both", expand=True)

        # output
        output_wrap = tk.Frame(v_pane, bg=DARK["output_bg"], height=210)
        v_pane.add(output_wrap, weight=1)

        out_header = tk.Frame(output_wrap, bg=DARK["output_bg"], height=28)
        out_header.pack(fill="x")
        out_header.pack_propagate(False)
        tk.Label(out_header, text="  OUTPUT", bg=DARK["output_bg"], fg=DARK["muted"],
                 font=("Segoe UI Semibold", 8)).pack(side="left", pady=6)
        tk.Button(out_header, text="clear", command=self.clear_output,
                  bg=DARK["output_bg"], fg=DARK["muted"],
                  activebackground=DARK["output_bg"], activeforeground="#fff",
                  bd=0, font=("Segoe UI", 8), cursor="hand2").pack(side="right", padx=12)

        self.output = tk.Text(
            output_wrap,
            background=DARK["output_bg"],
            foreground=DARK["output_fg"],
            insertbackground=DARK["output_fg"],
            font=("JetBrains Mono", 10) if "JetBrains Mono" in tkfont.families() else ("Consolas", 10),
            relief="flat", bd=0,
            padx=14, pady=8,
            state="disabled",
            wrap="word"
        )
        self.output.pack(fill="both", expand=True)

        # tag colors for output
        self.output.tag_configure("err", foreground=DARK["error"])
        self.output.tag_configure("ok", foreground=DARK["success"])
        self.output.tag_configure("muted", foreground=DARK["muted"])
        self.output.tag_configure("info", foreground=DARK["accent2"])

        # status bar
        status = ttk.Frame(self, style="Sidebar.TFrame", height=26)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)
        self.status_left = ttk.Label(status, text="ready • Xite v0.3 – X++", style="Status.TLabel")
        self.status_left.pack(side="left", padx=12)
        self.status_right = ttk.Label(status, text="Ln 1, Col 1  •  UTF-8  •  .xp", style="Status.TLabel")
        self.status_right.pack(side="right", padx=12)

        self.output_visible = True
        self.v_pane = v_pane
        self.output_wrap = output_wrap

    def _bind_keys(self):
        self.bind("<Control-s>", lambda e: (self.save_file(), "break"))
        self.bind("<Control-S>", lambda e: (self.save_file(), "break"))
        self.bind("<Control-o>", lambda e: (self.open_file_dialog(), "break"))
        self.bind("<F5>", lambda e: (self.run_file(), "break"))
        self.bind("<Control-r>", lambda e: (self.run_file(), "break"))
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<Control-Shift-p>", lambda e: (self.toggle_output(), "break"))
        # cursor position update
        self.bind_all("<<CursorMoved>>", lambda e: None)
    
    def _tick(self):
        # update cursor pos
        try:
            idx = self.editor.text.index("insert")
            line, col = idx.split(".")
            self.status_right.configure(text=f"Ln {line}, Col {int(col)+1}  •  {self.mode_var.get()}  •  Xite v0.3 – X++")
        except Exception:
            pass
        self.after(180, self._tick)

    # ---------- file ops ----------
    def open_folder(self):
        d = filedialog.askdirectory(initialdir=self.folder_root or REPO_ROOT)
        if d:
            self.folder_root = d
            self.file_tree.set_root(d)
            self._status(f"opened folder: {os.path.basename(d)}")

    def open_file_dialog(self):
        f = filedialog.askopenfilename(
            initialdir=self.folder_root,
            filetypes=[("X++ files","*.xp"), ("All files","*.*")]
        )
        if f:
            self.open_file_path(f)

    def open_file_path(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
            self.editor.set_text(txt)
            self.current_file = path
            self.dirty = False
            self._update_title()
            self._status(f"opened {os.path.basename(path)}")
            # auto-detect mode from file
            import re
            m = re.search(r'RNM\s*=\s*(\w+)', txt, re.I)
            if m:
                mode = m.group(1).upper()
                if mode in ("XCOM","XITR","ITR","AI"):
                    self.mode_var.set(mode if mode!="AI" else "ITR")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def save_file(self):
        if not self.current_file:
            return self.save_as()
        try:
            with open(self.current_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.editor.get_text())
            self.dirty = False
            self._update_title()
            self._status(f"saved • {os.path.basename(self.current_file)}", ok=True)
            return True
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return False

    def save_as(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".xp",
            filetypes=[("X++ files","*.xp"),("All files","*.*")],
            initialdir=self.folder_root
        )
        if not f: return False
        self.current_file = f
        return self.save_file()

    def _on_edit(self):
        if not self.dirty:
            self.dirty = True
            self._update_title()

    def _update_title(self):
        name = os.path.basename(self.current_file) if self.current_file else "untitled.xp"
        if self.dirty: name = "• " + name
        self.title(f"{name} — Xite v0.3 – X++")

    # ---------- run ----------
    def run_file(self):
        # auto save
        if self.current_file and self.dirty:
            if not self.save_file():
                return
        if not self.current_file:
            if not self.save_as():
                return
        mode = self.mode_var.get()
        # clear output
        self.clear_output()
        self._output(f"── X++ {mode} • {os.path.basename(self.current_file)} ──\n", "muted")
        self._status(f"running… [{mode}]")
        # run in thread
        threading.Thread(target=self._run_thread, args=(self.current_file, mode), daemon=True).start()

    def _run_thread(self, filepath, mode):
        try:
            # use xpp_core.cli directly to avoid PATH issues
            cmd = [sys.executable, "-m", "xpp_core.cli", "run", filepath, "--mode", mode, "--verbose"]
            env = os.environ.copy()
            # ensure repo root is importable
            repo = REPO_ROOT
            env["PYTHONPATH"] = repo + os.pathsep + env.get("PYTHONPATH","")
            start_t = time.time()
            proc = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(filepath) or repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                universal_newlines=True
            )
            self.proc = proc
            out_q = queue.Queue()
            def reader():
                assert proc.stdout is not None
                for line in proc.stdout:
                    out_q.put(line)
                proc.wait()
                out_q.put(None)
            threading.Thread(target=reader, daemon=True).start()
            # pump UI
            def pump():
                try:
                    while True:
                        try:
                            line = out_q.get_nowait()
                        except queue.Empty:
                            break
                        if line is None:
                            # done
                            elapsed = (time.time()-start_t)*1000
                            rc = proc.returncode
                            if rc == 0:
                                self._output(f"\n── done in {elapsed:.0f}ms ──\n", "ok")
                                self._status(f"finished • {elapsed:.0f}ms", ok=True)
                            else:
                                self._output(f"\n── exit {rc} • {elapsed:.0f}ms ──\n", "err")
                                self._status(f"exit {rc}", error=True)
                            self.proc = None
                            return
                        # colorize
                        tag = None
                        low = line.lower()
                        if "error" in low or "fatal" in low or "traceback" in low or "failed" in low:
                            tag = "err"
                        elif line.startswith("---") or line.startswith("[") or "x++" in low or "cache" in low:
                            tag = "muted"
                        self._output(line, tag)
                except Exception:
                    pass
                if self.proc:
                    self.after(50, pump)
            self.after(10, pump)
        except Exception as e:
            self._output(f"\n[IDE] launch failed: {e}\n", "err")

    def _output(self, text, tag=None):
        def _do():
            self.output.configure(state="normal")
            if tag:
                self.output.insert("end", text, tag)
            else:
                self.output.insert("end", text)
            self.output.see("end")
            self.output.configure(state="disabled")
        # thread-safe: schedule on main thread
        try:
            self.after(0, _do)
        except Exception:
            _do()

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def toggle_output(self):
        # crude toggle: forget / re-add
        # simpler: just focus editor
        self.editor.text.focus_set()

    def _status(self, msg, ok=False, error=False):
        def _set():
            self.status_left.configure(text=msg)
            if ok:
                self.status_left.configure(foreground=DARK["success"])
            elif error:
                self.status_left.configure(foreground=DARK["error"])
            else:
                self.status_left.configure(foreground=DARK["muted"])
            self.after(3500, lambda: self.status_left.configure(text=f"Xite v0.3 – X++ • {self.mode_var.get()}", foreground=DARK["muted"]))
        self.after(0, _set)


def main():
    app = XiteIDE()
    # center
    app.update_idletasks()
    w = 1280; h = 820
    sw = app.winfo_screenwidth(); sh = app.winfo_screenheight()
    x = (sw - w)//2; y = (sh - h)//2 - 20
    app.geometry(f"{w}x{h}+{x}+{y}")
    app.mainloop()

if __name__ == "__main__":
    main()
