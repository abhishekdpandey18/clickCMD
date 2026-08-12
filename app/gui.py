from __future__ import annotations

import copy
import json
import os
import queue
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from .button_editor import ButtonEditor
from .command_manager import CommandManager, looks_destructive
from .config_manager import ConfigManager
from .theme_manager import ThemeManager
from .version import __version__


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
    def show(self, _=None):
        if not self.text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.configure(bg="#080b13")
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip.geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg="#080b13", fg="#ffffff",
                 padx=9, pady=6, font=("TkDefaultFont", 9)).pack()
    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class CommandCenterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.manager = ConfigManager()
        self.config_data = self.manager.load()
        self.theme = ThemeManager(self.config_data["settings"].get("theme", "dark"))
        self.event_queue = queue.Queue()
        self.command_manager = CommandManager(self.event_queue.put)
        self.active_category = 0
        self.search_var = tk.StringVar()
        self.selected_button = None
        self.filter_mode = "all"
        self.history = self.config_data.get("history", [])
        self.drag_data = {"button": None, "widget": None, "start_y": 0}

        self.title("⚡ Command Center")
        self.minsize(900, 620)
        self.geometry(self.config_data["settings"].get("window_geometry", "1280x800"))
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._configure_ttk()
        self._build_ui()
        self._bind_shortcuts()
        self._apply_theme()
        self.after(60, self._process_events)
        self.after(100, self.refresh_dashboard)

    # ---------- Theme / UI ----------
    def _configure_ttk(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

    def _apply_theme(self):
        c = self.theme.colors
        self.configure(bg=c["bg"])
        self.style.configure("TNotebook", background=c["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=c["panel2"], foreground=c["muted"],
                             padding=(14, 8), borderwidth=0)
        self.style.map("TNotebook.Tab", background=[("selected", c["accent"])],
                       foreground=[("selected", "#ffffff")])
        self.style.configure("TCombobox", fieldbackground=c["input"], background=c["input"],
                             foreground=c["text"], arrowcolor=c["text"])
        self._refresh_static_colors()

    def _refresh_static_colors(self):
        if not hasattr(self, "root_frame"):
            return
        c = self.theme.colors
        for widget in (self.root_frame, self.header, self.sidebar, self.content, self.output_panel):
            widget.configure(bg=c["bg"] if widget in (self.root_frame, self.content) else c["panel"])
        self.search.configure(bg=c["input"], fg=c["text"], insertbackground=c["text"])
        self.output.configure(bg=c["input"], fg=c["text"], insertbackground=c["text"])
        self.category_title.configure(bg=c["panel"], fg=c["text"])
        self.title_label.configure(bg=c["panel"], fg=c["text"])
        self.subtitle.configure(bg=c["panel"], fg=c["muted"])
        self.output_title.configure(bg=c["panel"], fg=c["text"])
        self.status.configure(bg=c["panel"], fg=c["muted"])

    def _build_ui(self):
        c = self.theme.colors
        self.root_frame = tk.Frame(self, bg=c["bg"])
        self.root_frame.pack(fill="both", expand=True)

        self.header = tk.Frame(self.root_frame, bg=c["panel"], padx=24, pady=18)
        self.header.pack(fill="x")

        brand = tk.Frame(self.header, bg=c["panel"])
        brand.pack(side="left")
        self.title_label = tk.Label(brand, text="⚡ Command Center", bg=c["panel"], fg=c["text"],
                                    font=("TkDefaultFont", 22, "bold"))
        self.title_label.pack(anchor="w")
        self.subtitle = tk.Label(brand, text=f"Your commands. One beautiful dashboard.  •  v{__version__}",
                                 bg=c["panel"], fg=c["muted"], font=("TkDefaultFont", 10))
        self.subtitle.pack(anchor="w", pady=(2,0))

        actions = tk.Frame(self.header, bg=c["panel"])
        actions.pack(side="right", fill="y")
        self.search = tk.Entry(actions, textvariable=self.search_var, width=25,
                               bg=c["input"], fg=c["text"], insertbackground=c["text"],
                               relief="flat", bd=0, highlightthickness=1,
                               highlightbackground=c["border"], highlightcolor=c["accent"])
        self.search.pack(side="left", padx=(0,8), ipady=8)
        self.search.insert(0, "")
        Tooltip(self.search, "Search commands")
        self._action_button(actions, "＋ Add Button", self.add_button, c["accent"]).pack(side="left", padx=4)
        self._action_button(actions, "★ Favorites", self.toggle_favorites, c["panel2"]).pack(side="left", padx=4)
        self._action_button(actions, "◷ History", self.show_history, c["panel2"]).pack(side="left", padx=4)
        self._action_button(actions, "⚙ Settings", self.open_settings, c["panel2"]).pack(side="left", padx=4)

        self.body = tk.Frame(self.root_frame, bg=c["bg"])
        self.body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.body, bg=c["panel"], width=215, padx=14, pady=16)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.category_title = tk.Label(self.sidebar, text="CATEGORIES", bg=c["panel"], fg=c["text"],
                                       font=("TkDefaultFont", 9, "bold"), anchor="w")
        self.category_title.pack(fill="x", padx=8, pady=(0,10))
        self.category_list = tk.Frame(self.sidebar, bg=c["panel"])
        self.category_list.pack(fill="both", expand=True)
        self._build_category_list()

        self.content = tk.Frame(self.body, bg=c["bg"], padx=18, pady=18)
        self.content.pack(side="left", fill="both", expand=True)

        self.dashboard_canvas = tk.Canvas(self.content, bg=c["bg"], highlightthickness=0)
        self.dashboard_scroll = ttk.Scrollbar(self.content, orient="vertical", command=self.dashboard_canvas.yview)
        self.dashboard_canvas.configure(yscrollcommand=self.dashboard_scroll.set)
        self.dashboard_scroll.pack(side="right", fill="y")
        self.dashboard_canvas.pack(fill="both", expand=True)
        self.grid_frame = tk.Frame(self.dashboard_canvas, bg=c["bg"])
        self.canvas_window = self.dashboard_canvas.create_window((0,0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", self._on_grid_configure)
        self.dashboard_canvas.bind("<Configure>", self._on_canvas_configure)
        self.dashboard_canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.search_var.trace_add("write", lambda *_: self.refresh_dashboard())

        self.output_panel = tk.Frame(self.root_frame, bg=c["panel"], height=185, padx=18, pady=10)
        self.output_panel.pack(fill="x", side="bottom")
        self.output_panel.pack_propagate(False)
        out_head = tk.Frame(self.output_panel, bg=c["panel"])
        out_head.pack(fill="x")
        self.output_title = tk.Label(out_head, text="▸ Command Output", bg=c["panel"], fg=c["text"],
                                     font=("TkDefaultFont", 10, "bold"))
        self.output_title.pack(side="left")
        self.status = tk.Label(out_head, text="Ready", bg=c["panel"], fg=c["muted"],
                               font=("TkDefaultFont", 9))
        self.status.pack(side="left", padx=12)
        tk.Button(out_head, text="Clear", command=self.clear_output, bg=c["panel2"], fg=c["text"],
                  relief="flat", padx=10, cursor="hand2").pack(side="right")
        tk.Button(out_head, text="Copy", command=self.copy_output, bg=c["panel2"], fg=c["text"],
                  relief="flat", padx=10, cursor="hand2").pack(side="right", padx=5)

        self.output = tk.Text(self.output_panel, bg=c["input"], fg=c["text"], insertbackground=c["text"],
                              relief="flat", bd=0, wrap="word", font=("TkFixedFont", 9),
                              padx=10, pady=8)
        self.output.pack(fill="both", expand=True, pady=(7,0))
        self.output.tag_configure("stderr", foreground="#ff7b88")
        self.output.tag_configure("success", foreground=c["success"])
        self.output.tag_configure("command", foreground=c["accent"])

    def _action_button(self, parent, text, command, bg):
        c = self.theme.colors
        return tk.Button(parent, text=text, command=command, bg=bg,
                         fg="#ffffff" if bg == c["accent"] else c["text"],
                         activebackground=c["accent_hover"], activeforeground="#ffffff",
                         relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
                         font=("TkDefaultFont", 9, "bold"))

    def _on_grid_configure(self, _=None):
        self.dashboard_canvas.configure(scrollregion=self.dashboard_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.dashboard_canvas.itemconfigure(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if self.dashboard_canvas.winfo_containing(event.x_root, event.y_root):
            self.dashboard_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------- Categories ----------
    def _build_category_list(self):
        c = self.theme.colors
        for w in self.category_list.winfo_children():
            w.destroy()
        for i, cat in enumerate(self.config_data["categories"]):
            selected = i == self.active_category
            text = cat.get("name", "Category")
            btn = tk.Button(self.category_list, text=f"  {text}", anchor="w",
                            command=lambda idx=i: self.select_category(idx),
                            bg=c["accent"] if selected else c["panel"],
                            fg="#ffffff" if selected else c["muted"],
                            activebackground=c["accent"], activeforeground="#ffffff",
                            relief="flat", bd=0, padx=8, pady=10, cursor="hand2",
                            font=("TkDefaultFont", 10, "bold" if selected else "normal"))
            btn.pack(fill="x", pady=2)
            Tooltip(btn, f"{len(cat.get('buttons', []))} command(s)")
        sep = tk.Frame(self.category_list, bg=c["border"], height=1)
        sep.pack(fill="x", pady=12)
        self._sidebar_button("＋ New Category", self.new_category).pack(fill="x", pady=2)
        self._sidebar_button("✎ Rename Category", self.rename_category).pack(fill="x", pady=2)
        self._sidebar_button("− Delete Category", self.delete_category).pack(fill="x", pady=2)

    def _sidebar_button(self, text, command):
        c = self.theme.colors
        return tk.Button(self.category_list, text=text, command=command, anchor="w",
                         bg=c["panel"], fg=c["muted"], activebackground=c["panel2"],
                         activeforeground=c["text"], relief="flat", bd=0, padx=8, pady=8, cursor="hand2")

    def select_category(self, index):
        if 0 <= index < len(self.config_data["categories"]):
            self.active_category = index
            self.selected_button = None
            self._build_category_list()
            self.refresh_dashboard()

    def new_category(self):
        name = simpledialog.askstring("New category", "Category name:", parent=self)
        if name and name.strip():
            self.config_data["categories"].append({"name": name.strip(), "buttons": []})
            self.active_category = len(self.config_data["categories"]) - 1
            self.save_config()
            self._build_category_list()
            self.refresh_dashboard()

    def rename_category(self):
        if not self.config_data["categories"]:
            return
        current = self.config_data["categories"][self.active_category]["name"]
        name = simpledialog.askstring("Rename category", "New name:", initialvalue=current, parent=self)
        if name and name.strip():
            self.config_data["categories"][self.active_category]["name"] = name.strip()
            self.save_config()
            self._build_category_list()
            self.refresh_dashboard()

    def delete_category(self):
        if len(self.config_data["categories"]) <= 1:
            messagebox.showwarning("Cannot delete", "At least one category must remain.", parent=self)
            return
        cat = self.config_data["categories"][self.active_category]
        if cat.get("buttons") and not messagebox.askyesno(
            "Delete category", "This category contains commands. Delete it anyway?", parent=self
        ):
            return
        del self.config_data["categories"][self.active_category]
        self.active_category = max(0, self.active_category - 1)
        self.save_config()
        self._build_category_list()
        self.refresh_dashboard()

    # ---------- Dashboard ----------
    def current_category(self):
        return self.config_data["categories"][self.active_category]

    def filtered_buttons(self):
        query = self.search_var.get().strip().lower()
        buttons = self.current_category().get("buttons", [])
        if self.filter_mode == "favorites":
            buttons = [b for b in buttons if b.get("favorite", False)]
        if not query:
            return buttons
        return [b for b in buttons if query in b.get("name","").lower()
                or query in b.get("description","").lower()
                or query in b.get("command","").lower()]

    def refresh_dashboard(self):
        if not hasattr(self, "grid_frame"):
            return
        c = self.theme.colors
        for w in self.grid_frame.winfo_children():
            w.destroy()

        buttons = self.filtered_buttons()
        columns = max(1, int(self.config_data["settings"].get("columns", 4)))
        for col in range(columns):
            self.grid_frame.grid_columnconfigure(col, weight=1, uniform="cards")

        if not buttons:
            empty = tk.Frame(self.grid_frame, bg=c["bg"])
            empty.grid(row=0, column=0, columnspan=columns, sticky="nsew", pady=70)
            tk.Label(empty, text="⌁", bg=c["bg"], fg=c["muted"], font=("TkDefaultFont", 36)).pack()
            tk.Label(empty, text="No commands here", bg=c["bg"], fg=c["text"],
                     font=("TkDefaultFont", 15, "bold")).pack(pady=(6,2))
            tk.Label(empty, text="Add a command or switch categories.", bg=c["bg"], fg=c["muted"],
                     font=("TkDefaultFont", 10)).pack()
            return

        for idx, button in enumerate(buttons):
            row, col = divmod(idx, columns)
            card = self._make_command_card(self.grid_frame, button)
            card.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")

    def _make_command_card(self, parent, button):
        c = self.theme.colors
        bg = button.get("color", c["card"])
        fg = button.get("text_color", c["text"])
        frame = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=c["border"],
                         width=int(self.config_data["settings"].get("button_width",220)),
                         height=int(self.config_data["settings"].get("button_height",105)))
        frame.pack_propagate(False)

        top = tk.Frame(frame, bg=bg)
        top.pack(fill="x", padx=13, pady=(12,0))
        icon = tk.Label(top, text=button.get("icon","⚡"), bg=bg, fg=fg,
                        font=("TkDefaultFont", 18))
        icon.pack(side="left")
        name = tk.Label(top, text=button.get("name","Unnamed"), bg=bg, fg=fg,
                        font=("TkDefaultFont", 11, "bold"), anchor="w")
        name.pack(side="left", fill="x", expand=True, padx=(9,0))
        fav = tk.Label(top, text="★" if button.get("favorite", False) else "", bg=bg, fg="#ffd166",
                       font=("TkDefaultFont", 11))
        fav.pack(side="right")

        desc = tk.Label(frame, text=button.get("description",""), bg=bg, fg=fg,
                        font=("TkDefaultFont", 8), anchor="w", justify="left")
        desc.pack(fill="x", padx=13, pady=(5,0))

        mode = button.get("execution_mode","normal")
        mode_text = {"terminal":"TERMINAL", "background":"BACKGROUND", "wait":"WAIT", "normal":"RUN"}.get(mode, "RUN")
        badge = tk.Label(frame, text=f"  {mode_text}  ", bg=c["panel2"], fg=c["muted"],
                         font=("TkDefaultFont", 7, "bold"))
        badge.pack(side="left", padx=13, pady=(6,8))

        for widget in (frame, top, icon, name, desc, badge):
            widget.bind("<Button-1>", lambda e, b=button: self.run_button(b))
            widget.bind("<Button-3>", lambda e, b=button, w=frame: self.context_menu(e, b, w))
            widget.bind("<ButtonPress-2>", lambda e, b=button, w=frame: self.start_drag(e, b, w))
            widget.bind("<B2-Motion>", self.drag_motion)
            widget.bind("<ButtonRelease-2>", self.end_drag)
        Tooltip(frame, button.get("description","") or button.get("command",""))
        return frame

    # ---------- Drag and drop ----------
    def start_drag(self, event, button, widget):
        self.drag_data = {"button": button, "widget": widget, "start_y": event.y_root}

    def drag_motion(self, event):
        if self.drag_data["button"]:
            self.config(cursor="fleur")

    def end_drag(self, event):
        button = self.drag_data.get("button")
        self.config(cursor="")
        self.drag_data = {"button": None, "widget": None, "start_y": 0}
        if not button:
            return
        # Use pointer position to infer destination card index.
        widgets = [w for w in self.grid_frame.winfo_children() if isinstance(w, tk.Frame)]
        target = None
        for w in widgets:
            if w.winfo_y() <= event.y_root - self.grid_frame.winfo_rooty() <= w.winfo_y() + w.winfo_height():
                if w.winfo_x() <= event.x_root - self.grid_frame.winfo_rootx() <= w.winfo_x() + w.winfo_width():
                    target = w
                    break
        buttons = self.current_category()["buttons"]
        try:
            old = buttons.index(button)
        except ValueError:
            return
        if target is None:
            return
        # Find the button represented by the target widget by rebuilding from
        # current grid order; approximate with nearest row/column.
        columns = max(1, int(self.config_data["settings"].get("columns",4)))
        col = max(0, int((event.x_root - self.grid_frame.winfo_rootx()) / max(1, self.grid_frame.winfo_width()/columns)))
        row = max(0, int((event.y_root - self.grid_frame.winfo_rooty()) / max(1, self.config_data["settings"].get("button_height",105)+14)))
        new = min(len(buttons)-1, row*columns + col)
        if old != new:
            item = buttons.pop(old)
            buttons.insert(new, item)
            self.save_config()
            self.refresh_dashboard()

    # ---------- Context menu ----------
    def context_menu(self, event, button, widget):
        self.selected_button = button
        menu = tk.Menu(self, tearoff=0, bg=self.theme.colors["panel"], fg=self.theme.colors["text"],
                       activebackground=self.theme.colors["accent"], activeforeground="#ffffff")
        menu.add_command(label="▶  Run", command=lambda: self.run_button(button))
        menu.add_separator()
        menu.add_command(label="✎  Edit", command=lambda: self.edit_button(button))
        menu.add_command(label="⧉  Duplicate", command=lambda: self.duplicate_button(button))
        menu.add_command(label="↕  Move to category", command=lambda: self.move_button(button))
        menu.add_command(label="★  Remove from favorites" if button.get("favorite", False) else "★  Add to favorites",
                         command=lambda: self.toggle_favorite(button))
        menu.add_command(label="🎨  Change Color", command=lambda: self.quick_color(button))
        menu.add_command(label="★  Change Icon", command=lambda: self.quick_icon(button))
        menu.add_separator()
        menu.add_command(label="✕  Delete", command=lambda: self.delete_button(button))
        menu.tk_popup(event.x_root, event.y_root)

    def edit_button(self, button):
        ButtonEditor(self, self.theme, button=button, categories=self.config_data["categories"],
                     on_save=lambda data: self._replace_button(button, data),
                     on_delete=lambda b: self.delete_button(b, from_editor=True))

    def _replace_button(self, old, new):
        buttons = self.current_category()["buttons"]
        idx = buttons.index(old)
        buttons[idx] = new
        self.save_config()
        self.refresh_dashboard()

    def duplicate_button(self, button):
        copy_button = copy.deepcopy(button)
        copy_button["id"] = os.urandom(8).hex()
        copy_button["name"] = f"{button.get('name','Command')} Copy"
        self.current_category()["buttons"].append(copy_button)
        self.save_config()
        self.refresh_dashboard()

    def move_button(self, button):
        names = [c["name"] for c in self.config_data["categories"]]
        if len(names) < 2:
            return
        dialog = tk.Toplevel(self)
        dialog.title("Move command")
        dialog.geometry("360x180")
        dialog.configure(bg=self.theme.colors["bg"])
        c = self.theme.colors
        tk.Label(dialog, text=f"Move “{button.get('name')}” to:", bg=c["bg"], fg=c["text"],
                 font=("TkDefaultFont", 11, "bold")).pack(pady=(25,10))
        var = tk.StringVar(value=names[self.active_category])
        combo = ttk.Combobox(dialog, textvariable=var, values=names, state="readonly")
        combo.pack(fill="x", padx=30)
        def do_move():
            target = names.index(var.get())
            source = self.current_category()["buttons"]
            if target == self.active_category:
                dialog.destroy()
                return
            source.remove(button)
            self.config_data["categories"][target]["buttons"].append(button)
            self.save_config()
            dialog.destroy()
            self.refresh_dashboard()
            self._build_category_list()
        tk.Button(dialog, text="Move", command=do_move, bg=c["accent"], fg="white",
                  relief="flat", padx=18, pady=8).pack(pady=20)

    def quick_color(self, button):
        from tkinter import colorchooser
        result = colorchooser.askcolor(color=button.get("color", self.theme.colors["card"]), parent=self)
        if result and result[1]:
            button["color"] = result[1]
            self.save_config()
            self.refresh_dashboard()

    def quick_icon(self, button):
        value = simpledialog.askstring("Change icon", "Icon / emoji:", initialvalue=button.get("icon","⚡"), parent=self)
        if value is not None:
            button["icon"] = value or "⚡"
            self.save_config()
            self.refresh_dashboard()

    def delete_button(self, button, from_editor=False):
        if not messagebox.askyesno("Delete command", f"Delete “{button.get('name','')}”?\n\nThis cannot be undone.", parent=self):
            return
        buttons = self.current_category()["buttons"]
        if button in buttons:
            buttons.remove(button)
            self.selected_button = None
            self.save_config()
            self.refresh_dashboard()

    # ---------- Editors ----------
    def add_button(self):
        ButtonEditor(self, self.theme, categories=self.config_data["categories"], on_save=self._add_button_data)

    def _add_button_data(self, data):
        self.current_category()["buttons"].append(data)
        self.save_config()
        self.refresh_dashboard()

    def toggle_favorites(self):
        self.filter_mode = "all" if self.filter_mode == "favorites" else "favorites"
        self.refresh_dashboard()
        self.status.configure(text="Showing favorites" if self.filter_mode == "favorites" else "Showing all commands")

    def toggle_favorite(self, button):
        button["favorite"] = not button.get("favorite", False)
        self.save_config()
        self.refresh_dashboard()

    def show_history(self):
        win = tk.Toplevel(self)
        win.title(f"Command History — v{__version__}")
        win.geometry("760x480")
        c = self.theme.colors
        win.configure(bg=c["bg"])
        tk.Label(win, text="Command History", bg=c["bg"], fg=c["text"],
                 font=("TkDefaultFont", 18, "bold")).pack(anchor="w", padx=20, pady=(18,2))
        tk.Label(win, text="Recent commands launched from Command Center", bg=c["bg"], fg=c["muted"]).pack(anchor="w", padx=20, pady=(0,12))
        text = tk.Text(win, bg=c["input"], fg=c["text"], relief="flat", wrap="word",
                       font=("TkFixedFont", 9), padx=12, pady=10)
        text.pack(fill="both", expand=True, padx=20, pady=(0,12))
        for item in reversed(self.history):
            text.insert("end", f"[{item.get('time','')}]  {item.get('name','Command')}\n$ {item.get('command','')}\n\n")
        text.configure(state="disabled")
        tk.Button(win, text="Clear History", command=lambda: self.clear_history(win),
                  bg=c["danger"], fg="white", relief="flat", padx=14, pady=8).pack(anchor="e", padx=20, pady=(0,18))

    def clear_history(self, window=None):
        if not messagebox.askyesno("Clear history", "Delete all command history?", parent=window or self):
            return
        self.history = []
        self.config_data["history"] = []
        self.save_config()
        if window:
            window.destroy()

    def _record_history(self, button, command):
        from datetime import datetime
        self.history.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": button.get("name", "Command"),
            "command": command,
        })
        limit = int(self.config_data["settings"].get("history_limit", 50))
        self.history = self.history[:max(1, limit)]
        self.config_data["history"] = self.history
        self.save_config()

    # ---------- Command execution ----------
    def run_button(self, button):
        command = button.get("command","").strip()
        if looks_destructive(command):
            if not messagebox.askyesno(
                "Potentially destructive command",
                "This command appears capable of changing or deleting system data.\n\n"
                f"$ {command}\n\nContinue only if you trust this command.",
                parent=self,
            ):
                return
        try:
            self._record_history(button, command)
            self.command_manager.execute(button)
        except Exception as exc:
            self.show_command_error(str(exc), command)

    def _process_events(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                kind = event[0]
                if kind == "start":
                    _, button, command, mode = event
                    self.status.configure(text=f"Running: {button.get('name','Command')}")
                    self.output.insert("end", f"\n$ {command}\n", "command")
                    self.output.see("end")
                elif kind == "terminal":
                    self.status.configure(text="Opened terminal")
                    self.output.insert("end", "[Opened in terminal emulator]\n", "success")
                    self.output.see("end")
                elif kind == "output":
                    _, stream, line = event
                    self.output.insert("end", line, "stderr" if stream == "stderr" else None)
                    self.output.see("end")
                elif kind == "finish":
                    _, button, code, stdout, stderr, command = event
                    if code == 0:
                        self.status.configure(text=f"Finished successfully: {button.get('name','Command')}")
                        self.output.insert("end", f"\nProcess finished with exit code: {code}\n", "success")
                    else:
                        self.status.configure(text=f"Failed: {button.get('name','Command')}")
                        self.output.insert("end", f"\nProcess finished with exit code: {code}\n", "stderr")
                        if stderr:
                            self.output.insert("end", f"stderr:\n{stderr}\n", "stderr")
                    self.output.see("end")
                elif kind == "error":
                    _, button, error, command = event
                    self.show_command_error(error, command)
        except queue.Empty:
            pass
        self.after(60, self._process_events)

    def show_command_error(self, error, command):
        self.status.configure(text="Command error")
        self.output.insert("end", f"\nCommand failed\n$ {command}\n{error}\n", "stderr")
        self.output.see("end")
        messagebox.showerror("Command failed", f"Exit / error:\n\n{error}", parent=self)

    def clear_output(self):
        self.output.delete("1.0", "end")
        self.status.configure(text="Ready")

    def copy_output(self):
        text = self.output.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.configure(text="Output copied")

    # ---------- Settings ----------
    def open_settings(self):
        win = tk.Toplevel(self)
        win.title("Command Center Settings")
        win.geometry("650x650")
        win.minsize(600, 560)
        win.configure(bg=self.theme.colors["bg"])
        win.transient(self)
        c = self.theme.colors

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        appearance = tk.Frame(notebook, bg=c["bg"], padx=25, pady=20)
        config_tab = tk.Frame(notebook, bg=c["bg"], padx=25, pady=20)
        notebook.add(appearance, text="Appearance")
        notebook.add(config_tab, text="Configuration")

        tk.Label(appearance, text="Appearance", bg=c["bg"], fg=c["text"],
                 font=("TkDefaultFont", 18, "bold")).pack(anchor="w")
        tk.Label(appearance, text="Tune the dashboard to your setup.", bg=c["bg"], fg=c["muted"]).pack(anchor="w", pady=(3,20))

        theme_var = tk.StringVar(value=self.theme.mode)
        self._setting_row(appearance, "Theme", ttk.Combobox(appearance, textvariable=theme_var,
                          values=["dark","light"], state="readonly"))

        cols_var = tk.IntVar(value=int(self.config_data["settings"].get("columns",4)))
        self._setting_row(appearance, "Columns", tk.Spinbox(appearance, from_=1, to=8, textvariable=cols_var,
                          bg=c["input"], fg=c["text"], buttonbackground=c["panel2"], relief="flat"))

        font_var = tk.IntVar(value=int(self.config_data["settings"].get("font_size",11)))
        self._setting_row(appearance, "Font size", tk.Spinbox(appearance, from_=8, to=22, textvariable=font_var,
                          bg=c["input"], fg=c["text"], buttonbackground=c["panel2"], relief="flat"))

        width_var = tk.IntVar(value=int(self.config_data["settings"].get("button_width",220)))
        self._setting_row(appearance, "Button width", tk.Spinbox(appearance, from_=150, to=400, textvariable=width_var,
                          bg=c["input"], fg=c["text"], buttonbackground=c["panel2"], relief="flat"))

        height_var = tk.IntVar(value=int(self.config_data["settings"].get("button_height",105)))
        self._setting_row(appearance, "Button height", tk.Spinbox(appearance, from_=80, to=240, textvariable=height_var,
                          bg=c["input"], fg=c["text"], buttonbackground=c["panel2"], relief="flat"))

        def apply_appearance():
            self.config_data["settings"]["columns"] = cols_var.get()
            self.config_data["settings"]["font_size"] = font_var.get()
            self.config_data["settings"]["button_width"] = width_var.get()
            self.config_data["settings"]["button_height"] = height_var.get()
            if theme_var.get() != self.theme.mode:
                self.theme.mode = theme_var.get()
                self._apply_theme()
                self._build_category_list()
            self.save_config()
            self.refresh_dashboard()
            win.destroy()

        tk.Button(appearance, text="Apply appearance", command=apply_appearance,
                  bg=c["accent"], fg="white", relief="flat", padx=18, pady=10, cursor="hand2").pack(anchor="e", pady=25)

        tk.Label(config_tab, text="Configuration", bg=c["bg"], fg=c["text"],
                 font=("TkDefaultFont", 18, "bold")).pack(anchor="w")
        tk.Label(config_tab, text=f"Stored at  {self.manager.config_file}",
                 bg=c["bg"], fg=c["muted"], wraplength=540, justify="left").pack(anchor="w", pady=(4,22))

        self._settings_button(config_tab, "Export configuration", self.export_config)
        self._settings_button(config_tab, "Import configuration", self.import_config)
        self._settings_button(config_tab, "Create backup", self.create_backup)
        self._settings_button(config_tab, "Restore backup", self.restore_backup)
        self._settings_button(config_tab, "Reset to defaults", self.reset_config, danger=True)

    def _setting_row(self, parent, label, control):
        c = self.theme.colors
        row = tk.Frame(parent, bg=self.theme.colors["bg"])
        row.pack(fill="x", pady=8)
        tk.Label(row, text=label, bg=c["bg"], fg=c["text"], width=18, anchor="w").pack(side="left")
        control.pack(side="right", fill="x", expand=True, ipady=4)

    def _settings_button(self, parent, text, command, danger=False):
        c = self.theme.colors
        tk.Button(parent, text=text, command=command, anchor="w",
                  bg=c["danger"] if danger else c["panel2"], fg="#ffffff" if danger else c["text"],
                  activebackground=c["accent"], activeforeground="#ffffff",
                  relief="flat", padx=15, pady=11, cursor="hand2").pack(fill="x", pady=5)

    def export_config(self):
        path = filedialog.asksaveasfilename(parent=self, title="Export configuration",
                                            defaultextension=".json",
                                            filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path:
            return
        try:
            if os.path.exists(path) and not messagebox.askyesno("Overwrite?", "That file already exists. Overwrite it?", parent=self):
                return
            self.manager.export_to(path, self.config_data)
            messagebox.showinfo("Export complete", "Configuration exported successfully.", parent=self)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)

    def import_config(self):
        path = filedialog.askopenfilename(parent=self, title="Import configuration",
                                          filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path:
            return
        try:
            if not messagebox.askyesno("Import configuration",
                                       "Importing will replace the current dashboard. Continue?", parent=self):
                return
            self.config_data = self.manager.import_from(path)
            self.theme.mode = self.config_data["settings"].get("theme","dark")
            self._apply_theme()
            self.active_category = 0
            self.save_config()
            self._build_category_list()
            self.refresh_dashboard()
        except Exception as exc:
            messagebox.showerror("Import failed", f"Invalid configuration:\n\n{exc}", parent=self)

    def create_backup(self):
        try:
            self.save_config()
            path = self.manager.create_backup()
            messagebox.showinfo("Backup created", f"Backup saved to:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Backup failed", str(exc), parent=self)

    def restore_backup(self):
        path = filedialog.askopenfilename(parent=self, title="Restore backup",
                                          initialdir=str(self.manager.config_file.parent / "backups"),
                                          filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path:
            return
        if not messagebox.askyesno("Restore backup", "Replace the current configuration with this backup?", parent=self):
            return
        try:
            self.config_data = self.manager.restore_backup(path)
            self.theme.mode = self.config_data["settings"].get("theme","dark")
            self._apply_theme()
            self.active_category = 0
            self._build_category_list()
            self.refresh_dashboard()
        except Exception as exc:
            messagebox.showerror("Restore failed", str(exc), parent=self)

    def reset_config(self):
        if not messagebox.askyesno("Reset configuration",
                                   "Reset all categories, buttons and appearance settings to defaults?", parent=self):
            return
        self.config_data = self.manager.reset()
        self.theme.mode = self.config_data["settings"].get("theme","dark")
        self.save_config()
        self.active_category = 0
        self._apply_theme()
        self._build_category_list()
        self.refresh_dashboard()

    # ---------- Persistence / shortcuts ----------
    def save_config(self):
        self.config_data["settings"]["theme"] = self.theme.mode
        self.config_data["history"] = self.history[:int(self.config_data["settings"].get("history_limit", 50))]
        self.manager.save(self.config_data)

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.add_button())
        self.bind("<Control-f>", lambda e: (self.search.focus_set(), "break"))
        self.bind("<Control-s>", lambda e: self.save_config())
        self.bind("<Control-r>", lambda e: self.reload_config())
        self.bind("<F5>", lambda e: self.refresh_dashboard())
        self.bind("<Delete>", lambda e: self.delete_button(self.selected_button) if self.selected_button else None)

    def reload_config(self):
        self.config_data = self.manager.load()
        self.theme.mode = self.config_data["settings"].get("theme","dark")
        self.active_category = min(self.active_category, len(self.config_data["categories"])-1)
        self._apply_theme()
        self._build_category_list()
        self.refresh_dashboard()
        self.status.configure(text="Configuration reloaded")

    def on_close(self):
        self.config_data["settings"]["window_geometry"] = self.geometry()
        self.save_config()
        self.destroy()
