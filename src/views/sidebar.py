import flet as ft


def build_sidebar(expanded_content: ft.Control, on_close):
    drawer = ft.NavigationDrawer(width=360, controls=[])
    header = ft.Container(
        width=320,
        padding=12,
        gradient=ft.LinearGradient(
            colors=[ft.Colors.INDIGO_700, ft.Colors.PURPLE_700],
            rotation=0,
        ),
        animate=ft.Animation(duration=450, curve=ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Row([], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
    )

    def fold():
        drawer.width = 84
        header.width = 84
        header.content = ft.Row(
            [ft.IconButton(ft.Icons.MENU, tooltip="展开侧边栏", on_click=unfold)],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        drawer.controls = [header]
        drawer.update()

    def unfold():
        drawer.width = 360
        header.width = 320
        header.content = ft.Row(
            [
                ft.Text("菜品管理与设置", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.MENU_OPEN, tooltip="折叠侧边栏", on_click=fold),
                        ft.TextButton("完成", on_click=on_close),
                    ]
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        drawer.controls = [header, expanded_content]
        drawer.update()

    header.content = ft.Row(
        [
            ft.Text("菜品管理与设置", size=20, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    ft.IconButton(ft.Icons.MENU_OPEN, tooltip="折叠侧边栏", on_click=fold),
                    ft.TextButton("完成", on_click=on_close),
                ]
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    drawer.controls = [header, expanded_content]
    return drawer, header
