from __future__ import annotations

import os
import shlex
import subprocess
import threading
import re

from .terminal import launch_terminal

DESTRUCTIVE_PATTERNS = [
    r"(^|\s)rm(\s|$)",
    r"(^|\s)dd(\s|$)",
    r"(^|\s)mkfs(\.[\w-]+)?(\s|$)",
    r"(^|\s)shutdown(\s|$)",
    r"(^|\s)reboot(\s|$)",
    r"(^|\s)poweroff(\s|$)",
    r"(^|\s)halt(\s|$)",
    r"(^|\s)wipefs(\s|$)",
]

def expand_cwd(value):
    return os.path.abspath(os.path.expanduser(value or "~"))

def looks_destructive(command):
    lowered = command.lower()
    return any(re.search(pattern, lowered) for pattern in DESTRUCTIVE_PATTERNS)

def command_preview(command):
    return command.strip().replace("\n", " ")

class CommandManager:
    def __init__(self, on_event):
        self.on_event = on_event

    def execute(self, button):
        command = button.get("command", "").strip()
        if not command:
            raise ValueError("This button has no command configured.")

        mode = button.get("execution_mode", "normal")
        cwd = expand_cwd(button.get("working_directory", "~"))
        if not os.path.isdir(cwd):
            raise FileNotFoundError(f"Working directory does not exist:\n{cwd}")

        self.on_event(("start", button, command, mode))

        if mode == "terminal":
            launch_terminal(command, cwd)
            self.on_event(("terminal", button, command, mode))
            return

        if mode == "background":
            thread = threading.Thread(
                target=self._run,
                args=(button, command, cwd, False),
                daemon=True,
            )
            thread.start()
            return

        wait = mode == "wait"
        thread = threading.Thread(
            target=self._run,
            args=(button, command, cwd, wait),
            daemon=True,
        )
        thread.start()

    def _run(self, button, command, cwd, wait):
        try:
            # bash -lc is used deliberately so configured shell commands can
            # use pipes, redirects and shell scripts while still avoiding
            # shell=True in subprocess.Popen.
            process = subprocess.Popen(
                ["bash", "-lc", command],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self.on_event(("process", button, process.pid, command))

            stdout_chunks = []
            stderr_chunks = []

            def reader(stream, chunks, kind):
                for line in iter(stream.readline, ""):
                    chunks.append(line)
                    self.on_event(("output", kind, line))
                stream.close()

            t1 = threading.Thread(target=reader, args=(process.stdout, stdout_chunks, "stdout"), daemon=True)
            t2 = threading.Thread(target=reader, args=(process.stderr, stderr_chunks, "stderr"), daemon=True)
            t1.start()
            t2.start()

            code = process.wait()
            t1.join(timeout=2)
            t2.join(timeout=2)

            stdout = "".join(stdout_chunks)
            stderr = "".join(stderr_chunks)
            self.on_event(("finish", button, code, stdout, stderr, command))
        except Exception as exc:
            self.on_event(("error", button, str(exc), command))
