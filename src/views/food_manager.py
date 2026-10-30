import base64
import logging

import flet as ft
import flet_camera as fc

from food_storage import save_food_images, save_foods


log = logging.getLogger("app.views.food_manager")
_MAX_IMAGE_BYTES = 3 * 1024 * 1024


def build_food_manager(
    page: ft.Page,
    preferences: ft.SharedPreferences,
    file_picker: ft.FilePicker,
    food_dict: dict[str, list[str]],
    food_images: dict[str, dict[str, str]],
    on_categories_changed,
):
    status = ft.Text("")
    category_picker = ft.Dropdown(
        value=next(iter(food_dict)),
        options=[ft.DropdownOption(key=category, text=category) for category in food_dict],
    )
    new_food = ft.TextField(label="菜品名称", expand=True)
    new_category = ft.TextField(label="新分类名称", expand=True)
    rename_category = ft.TextField(label="修改当前分类名称", expand=True)
    food_list = ft.Column(spacing=8)

    async def persist(category=None, message="已保存。"):
        saved_foods = await save_foods(preferences, food_dict)
        saved_images = await save_food_images(preferences, food_images)
        status.value = message if saved_foods and saved_images else "已修改，但保存失败，请检查存储空间。"
        if category in food_dict:
            refresh_list(category)
        page.update()

    def save_image(category, food, image_bytes):
        async def apply_image():
            if not image_bytes:
                status.value = "没有读取到图片数据。"
            elif len(image_bytes) > _MAX_IMAGE_BYTES:
                status.value = "图片太大，请选择 3 MB 以内的图片。"
            else:
                food_images.setdefault(category, {})[food] = base64.b64encode(image_bytes).decode("ascii")
                await persist(category, f"已为「{food}」保存图片。")
                return
            page.update()

        return apply_image

    def image_actions(category, food):
        async def import_image():
            try:
                files = await file_picker.pick_files(
                    dialog_title=f"选择「{food}」的图片",
                    file_type=ft.FilePickerFileType.IMAGE,
                    allow_multiple=False,
                    with_data=True,
                    compression_quality=70,
                )
                if files and files[0].bytes:
                    await save_image(category, food, files[0].bytes)()
                elif files:
                    status.value = "没有读取到图片数据，请重试。"
                    page.update()
            except Exception:
                log.exception("Food image import failed")
                status.value = "导入失败，请确认图片权限后重试。"
                page.update()

        async def open_camera():
            camera = fc.Camera(width=320, height=240)
            camera_status = ft.Text("正在准备相机……")

            async def capture():
                try:
                    image_bytes = await camera.take_picture()
                    page.pop_dialog()
                    await save_image(category, food, image_bytes)()
                except Exception:
                    log.exception("Camera capture failed")
                    camera_status.value = "拍照失败，请检查相机权限后重试。"
                    page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"拍摄「{food}」的图片"),
                content=ft.Column([camera, camera_status], tight=True),
                actions=[
                    ft.TextButton("拍照并保存", on_click=capture),
                    ft.TextButton("取消", on_click=lambda: page.pop_dialog()),
                ],
            )
            page.show_dialog(dialog)
            page.update()
            try:
                cameras = await camera.get_available_cameras()
                if not cameras:
                    camera_status.value = "没有检测到可用相机。"
                else:
                    await camera.initialize(
                        cameras[0],
                        resolution_preset=fc.ResolutionPreset.MEDIUM,
                        enable_audio=False,
                    )
                    camera_status.value = "对准菜品后点击「拍照并保存」。"
            except Exception:
                log.exception("Camera initialization failed")
                camera_status.value = "无法打开相机，请检查设备权限或稍后重试。"
            page.update()

        return import_image, open_camera

    def refresh_list(category):
        rows = []
        for food in food_dict.get(category, []):
            encoded = food_images.get(category, {}).get(food)
            thumbnail = ft.Text("🍽️", size=24)
            if encoded:
                try:
                    thumbnail = ft.Image(
                        src=base64.b64decode(encoded),
                        width=56,
                        height=56,
                        fit=ft.BoxFit.COVER,
                    )
                except (ValueError, TypeError):
                    log.warning("Skipping invalid image for %s", food)
            import_image, open_camera = image_actions(category, food)

            async def remove_food(event, category=category, food=food):
                food_dict[category].remove(food)
                food_images.get(category, {}).pop(food, None)
                await persist(category, f"已删除「{food}」。")

            rows.append(
                ft.Column(
                    [
                        ft.Row(
                            [thumbnail, ft.Text(food)],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                ft.TextButton("导入图片", on_click=import_image),
                                ft.TextButton("拍照", on_click=open_camera),
                                ft.TextButton("删除菜品", on_click=remove_food),
                            ],
                            wrap=True,
                        ),
                    ],
                    spacing=2,
                )
            )
        if not rows:
            rows.append(ft.Text("当前分类还没有菜品。"))
        food_list.controls = rows

    async def add_food():
        item = (new_food.value or "").strip()
        category = category_picker.value
        if not item:
            status.value = "请先输入菜品名称。"
        elif item in food_dict[category]:
            status.value = "这个分类里已经有这道菜了。"
        else:
            food_dict[category].append(item)
            new_food.value = ""
            await persist(category, f"已在「{category}」添加「{item}」。")
            return
        page.update()

    async def add_category():
        name = (new_category.value or "").strip()
        if not name:
            status.value = "请输入分类名称。"
        elif name in food_dict:
            status.value = "这个分类已经存在。"
        else:
            food_dict[name] = []
            food_images[name] = {}
            category_picker.options = [
                ft.DropdownOption(key=category, text=category) for category in food_dict
            ]
            category_picker.value = name
            rename_category.value = name
            new_category.value = ""
            refresh_list(name)
            on_categories_changed()
            await persist(name, f"已创建分类「{name}」。")
            return
        page.update()

    async def rename_current_category():
        old = category_picker.value
        name = (rename_category.value or "").strip()
        if not name:
            status.value = "请输入新的分类名称。"
        elif name != old and name in food_dict:
            status.value = "这个分类名称已经存在。"
        elif name == old:
            status.value = "分类名称没有变化。"
        else:
            renamed = {}
            for category, items in food_dict.items():
                renamed[name if category == old else category] = items
            food_dict.clear()
            food_dict.update(renamed)
            if old in food_images:
                food_images[name] = food_images.pop(old)
            category_picker.options = [
                ft.DropdownOption(key=category, text=category) for category in food_dict
            ]
            category_picker.value = name
            rename_category.value = name
            refresh_list(name)
            on_categories_changed()
            await persist(name, f"分类已改名为「{name}」。")
            return
        page.update()

    async def delete_category():
        category = category_picker.value
        if len(food_dict) <= 1:
            status.value = "至少保留一个分类。"
        elif food_dict[category]:
            status.value = "请先删除这个分类里的菜品，再删除分类。"
        else:
            food_dict.pop(category)
            food_images.pop(category, None)
            category_picker.options = [
                ft.DropdownOption(key=name, text=name) for name in food_dict
            ]
            category_picker.value = next(iter(food_dict))
            rename_category.value = category_picker.value
            refresh_list(category_picker.value)
            on_categories_changed()
            await persist(category_picker.value, f"已删除空分类「{category}」。")
            return
        page.update()

    def category_changed(event):
        category = event.control.value
        rename_category.value = category
        refresh_list(category)
        status.value = ""
        page.update()

    category_picker.on_select = category_changed
    new_food.on_submit = lambda event: add_food()
    new_category.on_submit = lambda event: add_category()
    rename_category.value = category_picker.value
    refresh_list(category_picker.value)
    log.debug("Built food manager for %d categories", len(food_dict))

    return ft.Column(
        [
            ft.Text("菜品与分类管理", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("可添加、重命名分类，管理菜品并导入图片或拍照。"),
            category_picker,
            ft.Row([rename_category, ft.Button("重命名", on_click=rename_current_category)], wrap=True),
            ft.Row([new_category, ft.Button("添加分类", on_click=add_category)], wrap=True),
            ft.Row([new_food, ft.Button("添加菜品", on_click=add_food)], wrap=True),
            ft.TextButton("删除当前空分类", on_click=delete_category),
            status,
            food_list,
        ],
        spacing=12,
    )
