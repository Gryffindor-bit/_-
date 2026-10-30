import json
import logging
from datetime import datetime

import flet as ft


log = logging.getLogger("app.settings_storage")
_STORAGE_KEY = "today_eats_settings"
DEFAULT_SETTINGS = {
    "theme": "system",
    "lunch_time": "11:30",
    "dinner_time": "17:30",
    "countdown": 5,
}


def _valid_time(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%H:%M")
        return len(value) == 5
    except ValueError:
        return False


async def load_settings(preferences: ft.SharedPreferences) -> dict:
    saved = await preferences.get(_STORAGE_KEY)
    log.debug("Stored settings present: %s", saved is not None)
    if isinstance(saved, str):
        try:
            raw = json.loads(saved)
            if isinstance(raw, dict):
                settings = dict(DEFAULT_SETTINGS)
                theme = raw.get("theme")
                if theme in {"system", "light", "dark"}:
                    settings["theme"] = theme
                for key in ("lunch_time", "dinner_time"):
                    if _valid_time(raw.get(key)):
                        settings[key] = raw[key]
                try:
                    countdown = int(raw.get("countdown", DEFAULT_SETTINGS["countdown"]))
                    if 1 <= countdown <= 60:
                        settings["countdown"] = countdown
                except (TypeError, ValueError):
                    pass
                return settings
        except (json.JSONDecodeError, TypeError):
            pass
    return dict(DEFAULT_SETTINGS)


async def save_settings(preferences: ft.SharedPreferences, settings: dict) -> bool:
    return await preferences.set(_STORAGE_KEY, json.dumps(settings, ensure_ascii=False))
