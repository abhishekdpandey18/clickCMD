from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

TERMINALS = [
    ("xfce4-terminal", lambda cmd: ["xfce4-terminal", "--command", f"bash -lc {quote_for_terminal(cmd)}"]),
    ("konsole", lambda cmd: ["konsole", "-e", "bash", "-lc", cmd]),
    ("gnome-terminal", lambda cmd: ["gnome-terminal", "--", "bash", "-lc", cmd]),
    ("mate-terminal", lambda cmd: ["mate-terminal", "--", "bash", "-lc", cmd]),
    ("tilix", lambda cmd: ["tilix", "-e", f"bash -lc {quote_for_terminal(cmd)}"]),
    ("kitty", lambda cmd: ["kitty", "bash", "-lc", cmd]),
    ("alacritty", lambda cmd: ["alacritty", "-e", "bash", "-lc", cmd]),
]

def quote_for_terminal(command):
    # Quote a complete command for terminal emulators that accept one string.
    import shlex
    return shlex.quote(command)

def detect_terminal():
    preferred = os.environ.get("TERMINAL")
    candidates = [preferred] if preferred else []
    candidates += [name for name, _ in TERMINALS]
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            return candidate
    return None

def build_terminal_command(command):
    terminal = detect_terminal()
    if not terminal:
        raise RuntimeError("No supported terminal emulator was found.")
    for name, builder in TERMINALS:
        if terminal == name:
            return builder(command)
    return [terminal, "-e", "bash", "-lc", command]

def launch_terminal(command, cwd=None):
    args = build_terminal_command(command)
    return subprocess.Popen(args, cwd=cwd or None, start_new_session=True)
