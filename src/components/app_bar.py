# src/components/app_bar.py
import flet as ft
from utils.theme import ThemeManager


def create_app_bar(page: ft.Page, on_menu_click) -> ft.AppBar:
    """Constructs the top AppBar with menu toggle, title, and theme switch."""

    def handle_theme_change(e: ft.ControlEvent):
        ThemeManager.toggle_theme(page)

    return ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Toggle Sidebar",
            on_click=on_menu_click,
        ),
        leading_width=40,
        title=ft.Text("Student Portal", weight=ft.FontWeight.BOLD, size=20),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if hasattr(ft, "Colors") else "surfaceVariant",
        actions=[
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHT_MODE_OUTLINED, size=20),
                    ft.Switch(
                        value=page.theme_mode == ft.ThemeMode.DARK,
                        on_change=handle_theme_change,
                        tooltip="Toggle Light/Dark Theme",
                    ),
                    ft.Icon(ft.Icons.DARK_MODE_OUTLINED, size=20),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(width=16),
        ],
    )
