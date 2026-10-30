import logging

import flet as ft

from food_storage import save_foods


log = logging.getLogger("app.views.food_manager")


def build_food_manager(page: ft.Page, preferences: ft.SharedPreferences, food_dict: dict[str, list[str]]):
    status = ft.Text("")
    category_picker = ft.Dropdown(
        value=next(iter(food_dict)),
        options=[ft.DropdownOption(key=category, text=category) for category in food_dict],
    )
    new_food = ft.TextField(label="菜品名称", expand=True)
    food_list = ft.Column(spacing=4)

    def refresh_list(category):
        food_list.controls = [
            ft.Row(
                [
                    ft.Text(food, expand=True),
                    ft.TextButton("删除", on_click=remove_handler(category, food)),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            for food in food_dict[category]
        ]

    def remove_handler(category, item):
        async def remove_food():
            if len(food_dict[category]) <= 1:
                status.value = "每个分类至少保留一道菜。"
            else:
                food_dict[category].remove(item)
                saved = await save_foods(preferences, food_dict)
                status.value = "已删除并保存。" if saved else "已删除，但保存失败。"
                refresh_list(category)
            page.update()

        return remove_food

    async def add_food():
        item = (new_food.value or "").strip()
        category = category_picker.value
        if not item:
            status.value = "请先输入菜品名称。"
        elif item in food_dict[category]:
            status.value = "这个分类里已经有这道菜了。"
        else:
            food_dict[category].append(item)
            saved = await save_foods(preferences, food_dict)
            new_food.value = ""
            status.value = "已添加并保存。" if saved else "已添加，但保存失败。"
            refresh_list(category)
        page.update()

    def category_changed(event):
        refresh_list(event.control.value)
        status.value = ""
        page.update()

    category_picker.on_select = category_changed
    new_food.on_submit = lambda event: add_food()
    refresh_list(category_picker.value)
    log.debug("Built food manager for %d categories", len(food_dict))

    return ft.Column(
        [
            ft.Text("菜品管理", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("添加或删除菜品"),
            category_picker,
            ft.Row([new_food, ft.Button("添加", on_click=add_food)]),
            status,
            food_list,
        ],
        spacing=12,
    )
