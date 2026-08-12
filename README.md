# ⚡ Command Center

> A polished, customizable Linux desktop dashboard for launching shell commands and scripts.

Command Center turns your frequently used Linux commands, scripts and utilities into a clean visual dashboard.

![Platform](https://img.shields.io/badge/platform-Linux-111827)
![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)
![GUI](https://img.shields.io/badge/GUI-Tkinter-7C5CFF)
![License](https://img.shields.io/badge/license-MIT-22C55E)
![Status](https://img.shields.io/badge/status-v1.2.0-success)

## ✨ Features

- 🎛️ Custom command dashboard
- ➕ Add and edit commands through a GUI
- 🖱️ Reorder command cards
- 📂 Categories
- 🔎 Search
- 🎨 Custom button colors and emoji/icons
- 🖥️ Run commands normally or in a terminal
- ⚡ Background execution
- 📟 Live stdout/stderr output
- ⚠️ Confirmation for potentially destructive commands
- 💾 Automatic configuration persistence
- 📤 Import/export JSON
- 💿 Backup and restore
- 🌙 Dark and light themes
- ⌨️ Keyboard shortcuts
- 📝 Application error logging
- ★ Favorites filter and per-command favorites
- ◷ Persistent command history
- 🐧 Designed for Kali, Debian, Ubuntu, XFCE, KDE and GNOME

## 🖼️ Screenshots

Add screenshots here after taking them from your installation:

```text
docs/
├── dashboard.png
├── command-editor.png
└── settings.png
```

Then embed them in this README:

```markdown
![Command Center dashboard](docs/dashboard.png)
```

## 🚀 Installation

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/command-center.git
cd command-center
```

### 2. Install Tkinter

On Kali/Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3-tk
```

No third-party Python packages are required.

### 3. Run

```bash
python3 main.py
```

## 🆕 v1.2 highlights

- Favorite/pinned commands
- One-click Favorites filter
- Persistent command history with clear-history action
- v1.2 configuration migration for older configs
- Version shown in the application UI

## 🧪 Tests

Run the core smoke tests with:

```bash
python3 -m unittest discover -s tests -v
```

The GUI itself is intentionally not started by the automated tests.

## ⚙️ Configuration

Command Center stores its live configuration outside the repository:

```text
~/.config/command-center/
├── config.json
├── command-center.log
└── backups/
```

This means your personal commands do not need to be committed to GitHub.

An example configuration is included at:

```text
config/example-config.json
```

## 🎮 Execution modes

### Run normally

Captures command output in Command Center.

### Run in terminal

Opens the command using an available terminal emulator such as XFCE Terminal, Konsole or GNOME Terminal.

### Run in background

Starts the command without making the GUI wait for completion.

### Run and wait

Runs the command and reports the final exit status.

## 🛡️ Safety

Command Center does **not** execute configured commands automatically during startup.

Commands only execute after the user explicitly clicks a command.

Potentially destructive commands such as:

```text
rm
dd
mkfs
shutdown
reboot
poweroff
halt
wipefs
```

trigger a confirmation dialog.

The application does not automatically prepend `sudo`.

> Always review commands before adding them to your dashboard. Command Center is a launcher, not a sandbox.

## ⌨️ Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + N` | New command |
| `Ctrl + F` | Search |
| `Ctrl + S` | Save |
| `Ctrl + R` | Reload configuration |
| `Delete` | Delete selected command |
| `F5` | Refresh dashboard |

## 🖥️ Supported environments

Primarily developed for:

- Kali Linux
- Debian
- Ubuntu
- XFCE
- KDE Plasma
- GNOME

Terminal detection currently checks common Linux terminal emulators automatically.

## 📁 Project structure

```text
command-center/
│
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── command-center.desktop
│
├── app/
│   ├── __init__.py
│   ├── gui.py
│   ├── command_manager.py
│   ├── config_manager.py
│   ├── button_editor.py
│   ├── theme_manager.py
│   ├── terminal.py
│   └── version.py
│
├── assets/
│   └── icons/
│
├── config/
│   └── example-config.json
│
├── tests/
│   ├── __init__.py
│   └── test_core.py
│
└── .github/
    ├── pull_request_template.md
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

## 📦 Application-menu launcher

Copy `command-center.desktop` to:

```text
~/.local/share/applications/
```

Then change:

```ini
Exec=/usr/bin/python3 /absolute/path/to/command-center/main.py
```

to the actual absolute project path.

## 🧭 Roadmap

Possible future improvements:

- [ ] Custom SVG/PNG icons
- [ ] Better drag-and-drop animation
- [ ] Favorites/pinned commands
- [ ] Command history
- [ ] Per-command environment variables
- [ ] Multiple dashboard layouts
- [ ] Global hotkeys
- [ ] Plugin system
- [ ] Optional command scheduling
- [ ] More advanced command safety rules

## 🤝 Contributing

Pull requests and feature ideas are welcome.

For larger changes, open an issue first so the implementation can be discussed.

## 📄 License

Command Center is released under the MIT License.
