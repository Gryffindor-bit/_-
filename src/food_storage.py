import json
import logging

import flet as ft


log = logging.getLogger("app.food_storage")
_FOOD_KEY = "today_eats_foods"
_IMAGE_KEY = "today_eats_food_images"


async def load_foods(
    preferences: ft.SharedPreferences, defaults: dict[str, list[str]]
) -> dict[str, list[str]]:
    saved = await preferences.get(_FOOD_KEY)
    log.debug("Stored food data present: %s", saved is not None)
    if isinstance(saved, str):
        try:
            decoded = json.loads(saved)
            if isinstance(decoded, dict):
                foods = {}
                for category, items in decoded.items():
                    if isinstance(category, str) and category.strip() and isinstance(items, list):
                        foods[category.strip()] = [
                            item.strip()
                            for item in items
                            if isinstance(item, str) and item.strip()
                        ]
                if foods:
                    return foods
        except (json.JSONDecodeError, TypeError):
            log.warning("Could not read saved food data; using defaults")
    return {category: list(items) for category, items in defaults.items()}


async def save_foods(preferences: ft.SharedPreferences, foods: dict[str, list[str]]) -> bool:
    return await preferences.set(_FOOD_KEY, json.dumps(foods, ensure_ascii=False))


async def load_food_images(preferences: ft.SharedPreferences) -> dict[str, dict[str, str]]:
    saved = await preferences.get(_IMAGE_KEY)
    if isinstance(saved, str):
        try:
            decoded = json.loads(saved)
            if isinstance(decoded, dict):
                return {
                    category: {
                        food: image
                        for food, image in items.items()
                        if isinstance(food, str) and isinstance(image, str)
                    }
                    for category, items in decoded.items()
                    if isinstance(category, str) and isinstance(items, dict)
                }
        except (json.JSONDecodeError, TypeError):
            log.warning("Could not read saved food images")
    return {}


async def save_food_images(
    preferences: ft.SharedPreferences, images: dict[str, dict[str, str]]
) -> bool:
    return await preferences.set(_IMAGE_KEY, json.dumps(images, ensure_ascii=False))
