import json
import logging

import flet as ft


log = logging.getLogger("app.food_storage")
_STORAGE_KEY = "today_eats_foods"


async def load_foods(preferences: ft.SharedPreferences, defaults: dict[str, list[str]]) -> dict[str, list[str]]:
    saved = await preferences.get(_STORAGE_KEY)
    log.debug("Stored food data present: %s", saved is not None)
    if isinstance(saved, str):
        try:
            decoded = json.loads(saved)
            if isinstance(decoded, dict):
                foods = {}
                for category, default_items in defaults.items():
                    items = decoded.get(category, default_items)
                    if isinstance(items, list):
                        cleaned = [item.strip() for item in items if isinstance(item, str) and item.strip()]
                        foods[category] = cleaned or list(default_items)
                    else:
                        foods[category] = list(default_items)
                return foods
        except (json.JSONDecodeError, TypeError):
            pass
    return {category: list(items) for category, items in defaults.items()}


async def save_foods(preferences: ft.SharedPreferences, foods: dict[str, list[str]]) -> bool:
    return await preferences.set(_STORAGE_KEY, json.dumps(foods, ensure_ascii=False))
