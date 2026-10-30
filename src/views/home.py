import asyncio
import logging
import math
import random
import time
from datetime import datetime

import flet as ft

from food_storage import load_foods
from settings_storage import load_settings, save_settings
from views.food_manager import build_food_manager


log = logging.getLogger("app.views.home")
VERSION = "1.0.0"
AUTHOR = "Wen Xin"
DEFAULT_FOODS = {
    "米饭类": ["黄焖鸡米饭", "卤肉饭", "咖喱鸡饭", "番茄炒蛋盖饭", "鱼香肉丝盖饭", "辣子鸡饭"],
    "面食类": ["兰州拉面", "油泼面", "炸酱面", "螺蛳粉", "馄饨", "饺子", "炒面"],
    "小吃快餐": ["麻辣烫", "麻辣香锅", "烤串", "汉堡炸鸡", "米线", "酸辣粉"],
    "清淡养胃": ["粥+小菜", "蒸蛋", "清汤面", "蔬菜沙拉", "豆腐汤"],
}


async def build_home(page: ft.Page, preferences: ft.SharedPreferences):
    food_dict = await load_foods(preferences, DEFAULT_FOODS)
    settings = await load_settings(preferences)
    theme_modes = {
        "system": ft.ThemeMode.SYSTEM,
        "light": ft.ThemeMode.LIGHT,
        "dark": ft.ThemeMode.DARK,
    }
    page.theme_mode = theme_modes[settings["theme"]]
    log.debug("Loaded %d food categories and saved settings", len(food_dict))

    spinning = False
    wheel_angle = 0.0
    reminder_dialog_open = False
    last_reminded = {}

    result_text = ft.Text(
        "点下方按钮，开启抽签仪式！",
        size=22,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )
    draw_status = ft.Text("")
    settings_status = ft.Text("")
    wheel = ft.Container(
        content=ft.Text("🎡", size=64),
        rotate=ft.Rotate(angle=0),
        animate_rotation=ft.Animation(duration=150, curve=ft.AnimationCurve.LINEAR),
    )
    result_panel = ft.Container(
        content=result_text,
        rotate=ft.Rotate(angle=0),
        animate_rotation=ft.Animation(duration=80, curve=ft.AnimationCurve.EASE_IN_OUT),
    )
    theme_picker = ft.Dropdown(
        label="主题",
        value=settings["theme"],
        options=[
            ft.DropdownOption(key="system", text="跟随系统"),
            ft.DropdownOption(key="light", text="浅色模式"),
            ft.DropdownOption(key="dark", text="深色模式"),
        ],
    )
    lunch_time_field = ft.TextField(label="午餐提醒时间", value=settings["lunch_time"])
    dinner_time_field = ft.TextField(label="晚餐提醒时间", value=settings["dinner_time"])
    countdown_field = ft.TextField(
        label="抽签倒计时（1–60 秒）",
        value=str(settings["countdown"]),
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    def apply_theme(mode):
        page.theme_mode = theme_modes[mode]

    async def draw(category=None):
        nonlocal spinning, wheel_angle
        if spinning:
            return
        candidates = food_dict[category] if category else [item for values in food_dict.values() for item in values]
        if not candidates:
            draw_status.value = "这个分类还没有菜品。"
            page.update()
            return

        spinning = True
        spin_button.disabled = True
        for button in category_buttons:
            button.disabled = True
        draw_status.value = "转盘启动，倒计时揭晓……"
        page.update()

        duration = int(settings["countdown"])
        end_time = time.monotonic() + duration
        angle = wheel_angle
        while True:
            remaining = end_time - time.monotonic()
            if remaining <= 0:
                break
            progress = 1 - remaining / duration
            result_text.value = random.choice(candidates)
            draw_status.value = f"揭晓倒计时：{math.ceil(remaining)} 秒"
            angle += 0.72
            wheel.rotate = ft.Rotate(angle=angle)
            page.update()
            interval = 0.045 + 0.20 * progress**2
            await asyncio.sleep(min(interval, remaining))

        picked = random.choice(candidates)
        result_text.value = f"🎉 今天吃：\n{picked}" if category is None else f"✅【{category}】\n抽到：{picked}"
        draw_status.value = "抽签完成！"
        for shake_angle in (0.08, -0.08, 0.06, -0.06, 0):
            result_panel.rotate = ft.Rotate(angle=shake_angle)
            page.update()
            await asyncio.sleep(0.07)
        wheel_angle = angle + 0.35
        wheel.rotate = ft.Rotate(angle=wheel_angle)
        page.update()
        spin_button.disabled = False
        for button in category_buttons:
            button.disabled = False
        spinning = False
        page.update()

    async def draw_all():
        await draw()

    def category_handler(category):
        async def choose_category():
            await draw(category)

        return choose_category

    spin_button = ft.Button(
        "全部菜品随机抽",
        on_click=draw_all,
        bgcolor="#ff7744",
        color="white",
    )

    async def save_user_settings():
        try:
            lunch = datetime.strptime((lunch_time_field.value or "").strip(), "%H:%M").strftime("%H:%M")
            dinner = datetime.strptime((dinner_time_field.value or "").strip(), "%H:%M").strftime("%H:%M")
            countdown = int(countdown_field.value or "")
            if not 1 <= countdown <= 60:
                raise ValueError
        except ValueError:
            settings_status.value = "时间请用 HH:MM 格式，倒计时须为 1–60 秒。"
            page.update()
            return

        settings.update(
            lunch_time=lunch,
            dinner_time=dinner,
            countdown=countdown,
            theme=theme_picker.value,
        )
        lunch_time_field.value = lunch
        dinner_time_field.value = dinner
        saved = await save_settings(preferences, settings)
        settings_status.value = "设置已保存。" if saved else "保存失败，请重试。"
        page.update()

    async def theme_changed(event):
        settings["theme"] = event.control.value
        apply_theme(settings["theme"])
        saved = await save_settings(preferences, settings)
        settings_status.value = "主题已切换并保存。" if saved else "主题已切换，但保存失败。"
        page.update()

    theme_picker.on_select = theme_changed

    def show_reminder(meal_name):
        nonlocal reminder_dialog_open
        if not page.app_visible or reminder_dialog_open:
            return
        reminder_dialog_open = True

        async def start_drawing():
            nonlocal reminder_dialog_open
            page.pop_dialog()
            reminder_dialog_open = False
            await draw()

        def dismissed(event):
            nonlocal reminder_dialog_open
            reminder_dialog_open = False

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("该抽今天吃啥啦"),
                content=ft.Text(f"现在是{meal_name}时间，来抽一道今天的菜吧！"),
                actions=[ft.TextButton("开始抽签", on_click=start_drawing)],
                on_dismiss=dismissed,
            )
        )

    async def reminder_loop():
        while True:
            now = datetime.now()
            if page.app_visible:
                current_time = now.strftime("%H:%M")
                for meal_name, field in (
                    ("午餐", lunch_time_field),
                    ("晚餐", dinner_time_field),
                ):
                    reminder_key = (now.date(), meal_name)
                    if current_time == field.value and last_reminded.get(meal_name) != reminder_key:
                        last_reminded[meal_name] = reminder_key
                        show_reminder(meal_name)
            await asyncio.sleep(10)

    async def close_drawer():
        await home_view.close_drawer()

    async def open_drawer():
        await home_view.show_drawer()

    category_buttons = [
        ft.Button(category, on_click=category_handler(category), width=150)
        for category in food_dict
    ]
    drawer = ft.NavigationDrawer(
        width=360,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("菜品管理与设置", size=20, weight=ft.FontWeight.BOLD),
                                ft.TextButton("完成", on_click=close_drawer),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        build_food_manager(page, preferences, food_dict),
                        ft.Divider(),
                        ft.Text("主题与抽签", size=18, weight=ft.FontWeight.BOLD),
                        theme_picker,
                        lunch_time_field,
                        dinner_time_field,
                        countdown_field,
                        ft.Button("保存提醒和倒计时设置", on_click=save_user_settings),
                        settings_status,
                        ft.Divider(),
                        ft.Text("关于", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"今天吃什么  v{VERSION}\n作者：{AUTHOR}"),
                    ],
                    spacing=12,
                ),
            )
        ],
    )
    home_view = ft.View(
        scroll=ft.ScrollMode.AUTO,
        drawer=drawer,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.IconButton(ft.Icons.MENU, tooltip="打开菜品管理和设置", on_click=open_drawer),
                                ft.Text("🍜 今天吃什么", size=28, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Divider(),
                        wheel,
                        result_panel,
                        draw_status,
                        ft.Divider(),
                        spin_button,
                        ft.Row(category_buttons[:2], wrap=True, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row(category_buttons[2:], wrap=True, alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
            )
        ],
    )
    page.views.clear()
    page.views.append(home_view)
    page.update()
    asyncio.create_task(reminder_loop())
