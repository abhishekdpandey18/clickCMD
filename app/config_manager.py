from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / ".config" / "command-center"
CONFIG_FILE = APP_DIR / "config.json"
LOG_FILE = APP_DIR / "command-center.log"
BACKUP_DIR = APP_DIR / "backups"

DEFAULT_CONFIG = {
    "settings": {
        "theme": "dark",
        "columns": 4,
        "button_width": 220,
        "button_height": 105,
        "font_size": 11,
        "window_geometry": "1280x800",
        "background": "#0b1020",
        "accent": "#7c5cff",
        "show_output_panel": True,
        "history_limit": 50,
        "favorites_only": False,
    },
    "categories": [
        {
            "name": "System",
            "buttons": [
                {
                    "id": "terminal",
                    "name": "Open Terminal",
                    "command": "xfce4-terminal",
                    "description": "Open a terminal window.",
                    "icon": "💻",
                    "color": "#182235",
                    "text_color": "#ffffff",
                    "working_directory": "~",
                    "execution_mode": "normal",
                },
                {
                    "id": "files",
                    "name": "Open Home",
                    "command": "xdg-open ~",
                    "description": "Open your home directory.",
                    "icon": "📁",
                    "color": "#17261f",
                    "text_color": "#ffffff",
                    "working_directory": "~",
                    "execution_mode": "normal",
                },
            ],
        },
        {
            "name": "Scripts",
            "buttons": [],
        },
        {
            "name": "Security",
            "buttons": [],
        },
        {
            "name": "Video",
            "buttons": [],
        },
    ],
}


class ConfigManager:
    def __init__(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        if not CONFIG_FILE.exists():
            self.save(DEFAULT_CONFIG)

    def _setup_logging(self):
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
        )

    @staticmethod
    def _clone(data):
        return json.loads(json.dumps(data))

    def load(self):
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return self._merge_defaults(data)
        except Exception:
            logging.exception("Failed to load configuration; using defaults.")
            return self._clone(DEFAULT_CONFIG)

    def save(self, data):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".json.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            tmp.replace(CONFIG_FILE)
            logging.info("Configuration saved.")
            return True
        except Exception:
            logging.exception("Failed to save configuration.")
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            return False

    def _merge_defaults(self, data):
        result = self._clone(DEFAULT_CONFIG)
        if isinstance(data, dict):
            result["settings"].update(data.get("settings", {}))
            if isinstance(data.get("categories"), list):
                result["categories"] = data["categories"]
            # v1.2 migration: ensure every button has a stable favorite flag.
            for category in result["categories"]:
                category.setdefault("buttons", [])
                for button in category["buttons"]:
                    button.setdefault("favorite", False)
                    button.setdefault("description", "")
                    button.setdefault("icon", "⚡")
        return result

    def export_to(self, path, data):
        path = Path(path)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def import_from(self, path):
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return self._merge_defaults(data)

    def create_backup(self):
        if not CONFIG_FILE.exists():
            self.save(DEFAULT_CONFIG)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = BACKUP_DIR / f"config-{stamp}.json"
        shutil.copy2(CONFIG_FILE, target)
        return target

    def restore_backup(self, path):
        data = self.import_from(path)
        self.save(data)
        return data

    def reset(self):
        return self._clone(DEFAULT_CONFIG)

    @property
    def config_file(self):
        return CONFIG_FILE

    @property
    def log_file(self):
        return LOG_FILE
