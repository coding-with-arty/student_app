# src/utils/theme.py
import flet as ft


class ThemeManager:
    """Manages application-wide theme switching and Material Design 3 modes."""

    @staticmethod
    def toggle_theme(page: ft.Page) -> None:
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
        else:
            page.theme_mode = ft.ThemeMode.DARK
        page.update()
