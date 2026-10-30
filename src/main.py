import logging

import flet as ft

from views.home import build_home


LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)


async def main(page: ft.Page):
    page.title = "今天吃什么"
    page.window.width = 360
    page.window.height = 640
    preferences = ft.SharedPreferences()
    await build_home(page, preferences)


ft.run(main)
