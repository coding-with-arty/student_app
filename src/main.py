# src/main.py
import os
import flet as ft
from database.connection import init_db
from components.app_bar import create_app_bar
from utils.theme import apply_app_theme
from views.dashboard_view import DashboardView
from views.schedule_view import ScheduleView
from views.assignments_view import AssignmentsView
from views.degree_view import DegreeView
from views.contacts_view import ContactsView
from views.settings_view import SettingsView

# Resolve project root and assets directory paths dynamically
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")


def main(page: ft.Page):
    # Initialize SQLite database schema
    init_db()

    # Apply global theme defaults
    apply_app_theme(page)

    # Attach global App Bar
    page.appbar = create_app_bar(page, title="Student Portal")

    # Instantiate global FilePicker service on page session without adding to page.overlay
    global_file_picker = ft.FilePicker()
    page.file_picker = global_file_picker

    if hasattr(page, "services"):
        try:
            page.services.append(global_file_picker)
        except Exception:
            pass

    # Main view content container
    content_area = ft.Container(expand=True)

    # Navigation icons
    icon_dashboard = getattr(ft.Icons, "DASHBOARD_OUTLINE", getattr(ft.Icons, "DASHBOARD", "dashboard"))
    icon_schedule = getattr(ft.Icons, "CALENDAR_MONTH_OUTLINE", getattr(ft.Icons, "CALENDAR_MONTH", "calendar_month"))
    icon_assignments = getattr(ft.Icons, "ASSIGNMENT_OUTLINE", getattr(ft.Icons, "ASSIGNMENT", "assignment"))
    icon_degree = getattr(ft.Icons, "SCHOOL_OUTLINE", getattr(ft.Icons, "SCHOOL", "school"))
    icon_contacts = getattr(ft.Icons, "CONTACTS_OUTLINE", getattr(ft.Icons, "CONTACTS", "contacts"))
    icon_settings = getattr(ft.Icons, "SETTINGS_OUTLINE", getattr(ft.Icons, "SETTINGS", "settings"))

    views_dict = {
        0: lambda: DashboardView(page),
        1: lambda: ScheduleView(page),
        2: lambda: AssignmentsView(page),
        3: lambda: DegreeView(page),
        4: lambda: ContactsView(page),
        5: lambda: SettingsView(page),
    }

    def on_nav_change(e):
        selected_index = e.control.selected_index
        content_area.content = views_dict[selected_index]()
        content_area.update()

    cross_align_stretch = getattr(ft.CrossAxisAlignment, "STRETCH", "stretch")

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        leading=ft.Container(padding=10),
        destinations=[
            ft.NavigationRailDestination(
                icon=icon_dashboard,
                selected_icon=getattr(ft.Icons, "DASHBOARD", "dashboard"),
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=icon_schedule,
                selected_icon=getattr(ft.Icons, "CALENDAR_MONTH", "calendar_month"),
                label="Schedule",
            ),
            ft.NavigationRailDestination(
                icon=icon_assignments,
                selected_icon=getattr(ft.Icons, "ASSIGNMENT", "assignment"),
                label="Assignments",
            ),
            ft.NavigationRailDestination(
                icon=icon_degree,
                selected_icon=getattr(ft.Icons, "SCHOOL", "school"),
                label="Degree Path",
            ),
            ft.NavigationRailDestination(
                icon=icon_contacts,
                selected_icon=getattr(ft.Icons, "CONTACTS", "contacts"),
                label="Contacts",
            ),
            ft.NavigationRailDestination(
                icon=icon_settings,
                selected_icon=getattr(ft.Icons, "SETTINGS", "settings"),
                label="Settings",
            ),
        ],
        on_change=on_nav_change,
    )

    # Initial view load
    content_area.content = DashboardView(page)

    page.add(
        ft.Row(
            expand=True,
            vertical_alignment=cross_align_stretch,
            controls=[
                nav_rail,
                ft.VerticalDivider(width=1),
                content_area,
            ],
        )
    )
    page.update()


if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if hasattr(ft, "run"):
        ft.run(main, assets_dir=ASSETS_DIR)
    elif hasattr(ft, "app"):
        ft.app(target=main, assets_dir=ASSETS_DIR)
