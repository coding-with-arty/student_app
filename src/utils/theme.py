# src/utils/theme.py
import flet as ft


class ThemeManager:
    """Encapsulates theme state and Material Design 3 toggling for Flet v0.20+ applications."""

    @staticmethod
    def apply_theme(page: ft.Page) -> None:
        """Configures Material 3 seed colors and dark mode defaults on the Page instance."""
        page.title = "Student Portal"
        if page.theme_mode is None:
            page.theme_mode = ft.ThemeMode.DARK

        page.theme = ft.Theme(
            color_scheme_seed="blue",
            use_material3=True,
        )
        page.dark_theme = ft.Theme(
            color_scheme_seed="blue",
            use_material3=True,
        )

    @staticmethod
    def toggle_theme(page: ft.Page) -> ft.ThemeMode:
        """Toggles page theme between Dark and Light modes and refreshes UI."""
        page.theme_mode = (
            ft.ThemeMode.LIGHT
            if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        page.update()
        return page.theme_mode

    @staticmethod
    def get_toggle_icon(page: ft.Page):
        """Returns the active icon corresponding to current theme mode."""
        icon_dark = getattr(ft.Icons, "DARK_MODE", "dark_mode")
        icon_light = getattr(ft.Icons, "LIGHT_MODE", "light_mode")
        return icon_light if page.theme_mode == ft.ThemeMode.DARK else icon_dark


def apply_app_theme(page: ft.Page) -> None:
    """Module-level alias for ThemeManager.apply_theme."""
    ThemeManager.apply_theme(page)


def pad_symmetric(horizontal: float = 0, vertical: float = 0):
    """Cross-version symmetric padding helper."""
    if hasattr(ft, "padding") and hasattr(ft.padding, "symmetric"):
        try:
            return ft.padding.symmetric(horizontal=horizontal, vertical=vertical)
        except Exception:
            pass
    if hasattr(ft, "padding") and hasattr(ft.padding, "only"):
        try:
            return ft.padding.only(
                left=horizontal, right=horizontal, top=vertical, bottom=vertical
            )
        except Exception:
            pass
    return 0


def align_center():
    """Cross-version center alignment helper."""
    if hasattr(ft, "Alignment"):
        return ft.Alignment(0, 0)
    return "center"
