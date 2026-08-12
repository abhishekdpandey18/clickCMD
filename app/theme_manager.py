class ThemeManager:
    DARK = {
        "bg": "#0b1020",
        "panel": "#11182a",
        "panel2": "#151e32",
        "card": "#182235",
        "card_hover": "#202c46",
        "text": "#f4f7ff",
        "muted": "#8f9bb3",
        "accent": "#7c5cff",
        "accent_hover": "#947bff",
        "border": "#29344d",
        "danger": "#e95c6b",
        "success": "#41d6a0",
        "input": "#0d1424",
    }
    LIGHT = {
        "bg": "#eef2f8",
        "panel": "#ffffff",
        "panel2": "#f5f7fb",
        "card": "#ffffff",
        "card_hover": "#e9edfa",
        "text": "#182033",
        "muted": "#647089",
        "accent": "#6751e8",
        "accent_hover": "#7d69f2",
        "border": "#d7ddea",
        "danger": "#c83d4d",
        "success": "#13966d",
        "input": "#f7f9fd",
    }

    def __init__(self, mode="dark"):
        self.mode = mode if mode in ("dark", "light") else "dark"

    @property
    def colors(self):
        return self.DARK if self.mode == "dark" else self.LIGHT

    def toggle(self):
        self.mode = "light" if self.mode == "dark" else "dark"
        return self.colors
