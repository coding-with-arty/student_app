# src/views/dashboard_view.py
import flet as ft
from database.crud import get_courses, get_assignments, get_degree_requirements


class DashboardView(ft.Container):
    """Main application dashboard displaying academic metrics and course overview."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.app_page = page

        courses = get_courses()
        assignments = get_assignments()
        degree_reqs = get_degree_requirements()

        pending_assignments = [a for a in assignments if a.status != "Done"]
        completed_reqs = [r for r in degree_reqs if r.status == "Completed"]

        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Overview of your current academic status", color=ft.Colors.SECONDARY if hasattr(ft, "Colors") else "secondary"),
                ft.Divider(height=1),
                ft.ResponsiveRow(
                    controls=[
                        ft.Card(
                            col={"xs": 12, "sm": 4},
                            content=ft.Container(
                                padding=20,
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.BOOK, size=32, color=ft.Colors.BLUE if hasattr(ft, "Colors") else "blue"),
                                        ft.Text("Active Courses", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{len(courses)} Enrolled", size=22, weight=ft.FontWeight.BOLD),
                                    ]
                                ),
                            ),
                        ),
                        ft.Card(
                            col={"xs": 12, "sm": 4},
                            content=ft.Container(
                                padding=20,
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.ASSIGNMENT, size=32, color=ft.Colors.AMBER if hasattr(ft, "Colors") else "amber"),
                                        ft.Text("Pending Assignments", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{len(pending_assignments)} Due Soon", size=22, weight=ft.FontWeight.BOLD),
                                    ]
                                ),
                            ),
                        ),
                        ft.Card(
                            col={"xs": 12, "sm": 4},
                            content=ft.Container(
                                padding=20,
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.GRADE, size=32, color=ft.Colors.GREEN if hasattr(ft, "Colors") else "green"),
                                        ft.Text("Completed Requirements", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{len(completed_reqs)} / {len(degree_reqs)} Passed", size=22, weight=ft.FontWeight.BOLD),
                                    ]
                                ),
                            ),
                        ),
                    ]
                ),
                ft.Text("Enrolled Courses", size=20, weight=ft.FontWeight.BOLD),
                ft.ResponsiveRow(
                    controls=[
                        ft.Card(
                            col={"xs": 12, "sm": 6, "md": 3},
                            content=ft.Container(
                                padding=15,
                                border=ft.Border(left=ft.BorderSide(6, c.color)),
                                content=ft.Column(
                                    controls=[
                                        ft.Text(c.code, weight=ft.FontWeight.BOLD, size=16),
                                        ft.Text(c.title, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(c.professor, size=12, color=ft.Colors.SECONDARY if hasattr(ft, "Colors") else "secondary"),
                                    ]
                                ),
                            ),
                        )
                        for c in courses
                    ]
                ),
            ],
        )
