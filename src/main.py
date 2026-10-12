# src/main.py
import sys
from pathlib import Path

# Ensure 'src' directory is in Python module search path
src_dir = Path(__file__).parent.resolve()
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import flet as ft
from components.app_bar import create_app_bar
from database.connection import init_db
from views.assignments_view import AssignmentsView
from views.dashboard_view import DashboardView
from views.degree_view import DegreeView
from views.schedule_view import ScheduleView
from views.settings_view import SettingsView


def main(page: ft.Page):
    # Initialize SQLite database and seed initial records
    init_db()

    page.title = "Student App Portal"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    route_indices = {
        "/": 0,
        "/dashboard": 0,
        "/schedule": 1,
        "/degree": 2,
        "/assignments": 3,
        "/settings": 4,
    }

    index_routes = {
        0: "/dashboard",
        1: "/schedule",
        2: "/degree",
        3: "/assignments",
        4: "/settings",
    }

    def navigate_to(target_route: str):
        """Cross-version navigation helper supporting Flet 0.20+ and Flet 1.0+."""
        page.route = target_route
        if hasattr(page, "navigate") and callable(getattr(page, "navigate")):
            try:
                page.navigate(target_route)
                return
            except Exception:
                pass
        if hasattr(page, "go") and callable(getattr(page, "go")):
            try:
                page.go(target_route)
                return
            except Exception:
                pass
        if page.on_route_change:
            page.on_route_change(ft.RouteChangeEvent(route=target_route))

    def get_view_for_route(route: str) -> ft.Control:
        if route in ("/", "/dashboard"):
            return DashboardView(page)
        elif route == "/schedule":
            return ScheduleView(page)
        elif route == "/degree":
            return DegreeView(page)
        elif route == "/assignments":
            return AssignmentsView(page)
        elif route == "/settings":
            return SettingsView(page)
        return DashboardView(page)

    def on_nav_change(e: ft.ControlEvent):
        selected_index = e.control.selected_index
        target_route = index_routes.get(selected_index, "/dashboard")
        navigate_to(target_route)

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=72,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                selected_icon=ft.Icons.CALENDAR_MONTH,
                label="Schedule",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SCHOOL_OUTLINED,
                selected_icon=ft.Icons.SCHOOL,
                label="Degree Path",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ASSIGNMENT_OUTLINED,
                selected_icon=ft.Icons.ASSIGNMENT,
                label="Assignments",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Settings",
            ),
        ],
        on_change=on_nav_change,
    )

    def toggle_sidebar(e: ft.ControlEvent):
        nav_rail.extended = not nav_rail.extended
        nav_rail.update()

    def on_route_change(e: ft.RouteChangeEvent):
        nav_rail.selected_index = route_indices.get(e.route, 0)
        main_content = get_view_for_route(e.route)

        layout = ft.Row(
            expand=True,
            controls=[
                nav_rail,
                ft.VerticalDivider(width=1),
                main_content,
            ],
        )

        page.views.clear()
        page.views.append(
            ft.View(
                route=e.route,
                appbar=create_app_bar(page, on_menu_click=toggle_sidebar),
                controls=[layout],
                padding=0,
            )
        )
        page.update()

    def on_view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        navigate_to(top_view.route)

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop

    initial_target = page.route if page.route and page.route != "/" else "/dashboard"
    navigate_to(initial_target)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
    else:
        import flet as ft
        ft.run(main)
