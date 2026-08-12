from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, messagebox
from uuid import uuid4

class ButtonEditor(tk.Toplevel):
    MODES = [
        ("Run normally", "normal"),
        ("Run in terminal", "terminal"),
        ("Run in background", "background"),
        ("Run and wait for completion", "wait"),
    ]

    def __init__(self, parent, theme, button=None, categories=None, on_save=None, on_delete=None):
        super().__init__(parent)
        self.parent = parent
        self.theme = theme
        self.c = theme.colors
        self.original = button or {}
        self.categories = categories or []
        self.on_save = on_save
        self.on_delete = on_delete
        self.title("Edit Command" if button else "New Command")
        self.geometry("620x690")
        self.minsize(560, 620)
        self.configure(bg=self.c["bg"])
        self.transient(parent)
        self.grab_set()
        self._build()
        self._center()

    def _center(self):
        self.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - self.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x,0)}+{max(y,0)}")

    def _label(self, parent, text):
        tk.Label(parent, text=text, bg=self.c["bg"], fg=self.c["text"],
                 font=("TkDefaultFont", 10, "bold"), anchor="w").pack(fill="x", pady=(8,4))

    def _entry(self, parent, value="", show=None):
        e = tk.Entry(parent, bg=self.c["input"], fg=self.c["text"], insertbackground=self.c["text"],
                     relief="flat", bd=0, highlightthickness=1,
                     highlightbackground=self.c["border"], highlightcolor=self.c["accent"],
                     font=("TkDefaultFont", 11), show=show)
        e.insert(0, value)
        e.pack(fill="x", ipady=8)
        return e

    def _build(self):
        body = tk.Frame(self, bg=self.c["bg"], padx=28, pady=22)
        body.pack(fill="both", expand=True)

        title = tk.Label(body, text="Edit command" if self.original else "Create command",
                         bg=self.c["bg"], fg=self.c["text"], font=("TkDefaultFont", 20, "bold"))
        title.pack(anchor="w")
        tk.Label(body, text="Configure exactly what this dashboard button should do.",
                 bg=self.c["bg"], fg=self.c["muted"], font=("TkDefaultFont", 10)).pack(anchor="w", pady=(3,12))

        self._label(body, "Button name")
        self.name = self._entry(body, self.original.get("name",""))

        self._label(body, "Command")
        self.command = self._entry(body, self.original.get("command",""))

        self._label(body, "Description / tooltip")
        self.description = self._entry(body, self.original.get("description",""))

        row = tk.Frame(body, bg=self.c["bg"])
        row.pack(fill="x")
        left = tk.Frame(row, bg=self.c["bg"])
        left.pack(side="left", fill="x", expand=True, padx=(0,8))
        right = tk.Frame(row, bg=self.c["bg"])
        right.pack(side="left", fill="x", expand=True, padx=(8,0))

        self._label(left, "Icon / Emoji")
        self.icon = self._entry(left, self.original.get("icon","⚡"))
        self._label(right, "Working directory")
        self.cwd = self._entry(right, self.original.get("working_directory","~"))

        self.favorite_var = tk.BooleanVar(value=bool(self.original.get("favorite", False)))
        tk.Checkbutton(body, text="★ Add to Favorites", variable=self.favorite_var,
                       bg=self.c["bg"], fg=self.c["text"], selectcolor=self.c["panel2"],
                       activebackground=self.c["bg"], activeforeground=self.c["text"],
                       font=("TkDefaultFont", 10)).pack(anchor="w", pady=(10,2))

        self._label(body, "Execution mode")
        self.mode_var = tk.StringVar(value=self.original.get("execution_mode","normal"))
        mode = tk.Frame(body, bg=self.c["input"], highlightthickness=1, highlightbackground=self.c["border"])
        mode.pack(fill="x", pady=(0,2))
        for label, value in self.MODES:
            tk.Radiobutton(mode, text=label, value=value, variable=self.mode_var,
                           bg=self.c["input"], fg=self.c["text"], selectcolor=self.c["panel2"],
                           activebackground=self.c["input"], activeforeground=self.c["text"],
                           font=("TkDefaultFont", 10)).pack(side="left", padx=8, pady=9)

        colors = tk.Frame(body, bg=self.c["bg"])
        colors.pack(fill="x")
        self.bg_color = self._color_field(colors, "Background color", self.original.get("color","#182235"), left=True)
        self.text_color = self._color_field(colors, "Text color", self.original.get("text_color","#ffffff"), left=False)

        buttons = tk.Frame(body, bg=self.c["bg"])
        buttons.pack(fill="x", side="bottom", pady=(20,0))
        if self.original:
            tk.Button(buttons, text="Delete", command=self._delete,
                      bg=self.c["danger"], fg="white", relief="flat", padx=18, pady=10,
                      cursor="hand2").pack(side="left")
        tk.Button(buttons, text="Cancel", command=self.destroy,
                  bg=self.c["panel2"], fg=self.c["text"], relief="flat", padx=18, pady=10,
                  cursor="hand2").pack(side="right", padx=(8,0))
        tk.Button(buttons, text="Save Command", command=self._save,
                  bg=self.c["accent"], fg="white", relief="flat", padx=18, pady=10,
                  cursor="hand2").pack(side="right")

    def _color_field(self, parent, label, value, left=True):
        frame = tk.Frame(parent, bg=self.c["bg"])
        frame.pack(side="left", fill="x", expand=True, padx=(0,8) if left else (8,0))
        self._label(frame, label)
        inner = tk.Frame(frame, bg=self.c["input"])
        inner.pack(fill="x")
        entry = tk.Entry(inner, bg=self.c["input"], fg=self.c["text"], insertbackground=self.c["text"],
                         relief="flat", bd=0, font=("TkDefaultFont", 10))
        entry.insert(0, value)
        entry.pack(side="left", fill="x", expand=True, padx=8, ipady=8)
        tk.Button(inner, text="Pick", command=lambda: self._pick_color(entry),
                  bg=self.c["panel2"], fg=self.c["text"], relief="flat", padx=10,
                  cursor="hand2").pack(side="right", padx=4, pady=4)
        return entry

    def _pick_color(self, entry):
        result = colorchooser.askcolor(color=entry.get(), parent=self)
        if result and result[1]:
            entry.delete(0, "end")
            entry.insert(0, result[1])

    def _save(self):
        name = self.name.get().strip()
        command = self.command.get().strip()
        if not name or not command:
            messagebox.showwarning("Missing information", "Button name and command are required.", parent=self)
            return
        data = {
            "id": self.original.get("id", uuid4().hex),
            "name": name,
            "command": command,
            "description": self.description.get().strip(),
            "icon": self.icon.get().strip() or "⚡",
            "color": self.bg_color.get().strip() or "#182235",
            "text_color": self.text_color.get().strip() or "#ffffff",
            "working_directory": self.cwd.get().strip() or "~",
            "execution_mode": self.mode_var.get(),
            "favorite": self.favorite_var.get(),
        }
        if self.on_save:
            self.on_save(data)
        self.destroy()

    def _delete(self):
        if self.on_delete and messagebox.askyesno("Delete command", f"Delete “{self.original.get('name','')}”?", parent=self):
            self.on_delete(self.original)
            self.destroy()
