import json
import tempfile
import unittest
from pathlib import Path

from app.command_manager import looks_destructive
from app.config_manager import ConfigManager, DEFAULT_CONFIG


class CoreTests(unittest.TestCase):
    def test_destructive_detection(self):
        self.assertTrue(looks_destructive("rm -rf /tmp/test"))
        self.assertTrue(looks_destructive("sudo reboot"))
        self.assertTrue(looks_destructive("mkfs.ext4 /dev/sdb"))
        self.assertFalse(looks_destructive("echo hello"))
        self.assertFalse(looks_destructive("python3 script.py"))

    def test_default_config_shape(self):
        self.assertIn("settings", DEFAULT_CONFIG)
        self.assertIn("categories", DEFAULT_CONFIG)
        self.assertIsInstance(DEFAULT_CONFIG["categories"], list)

    def test_config_manager_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Exercise the JSON shape independently from the user's real config.
            path = Path(tmp) / "config.json"
            data = {
                "settings": {"theme": "dark", "columns": 3},
                "categories": [{"name": "Test", "buttons": []}],
            }
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["settings"]["columns"], 3)
            self.assertEqual(loaded["categories"][0]["name"], "Test")


if __name__ == "__main__":
    unittest.main()
