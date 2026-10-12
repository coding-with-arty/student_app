# src/components/app_bar.py
import flet as ft
from utils.theme import ThemeManager


def create_app_bar(page: ft.Page, title: str = "Student Portal") -> ft.AppBar:
    """Creates a standardized App Bar component with dynamic theme toggling via ThemeManager."""
    icon_school = getattr(ft.Icons, "SCHOOL", "school")

    def handle_theme_toggle(e):
        ThemeManager.toggle_theme(page)
        e.control.icon = ThemeManager.get_toggle_icon(page)
        e.control.update()

    return ft.AppBar(
        leading=ft.Icon(icon_school, size=24, color="primary"),
        leading_width=40,
        title=ft.Text(title, weight=ft.FontWeight.BOLD, size=20),
        center_title=False,
        bgcolor=getattr(ft.Colors, "SURFACE_CONTAINER_HIGHEST", "surfaceVariant"),
        actions=[
            ft.IconButton(
                icon=ThemeManager.get_toggle_icon(page),
                tooltip="Toggle Dark/Light Theme",
                on_click=handle_theme_toggle,
            ),
        ],
    )
