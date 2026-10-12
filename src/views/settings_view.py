# src/views/settings_view.py
import flet as ft
from database.crud import get_student_profile, update_student_profile


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


def create_primary_button(text: str, icon=None, on_click=None) -> ft.Container:
    """Version-agnostic primary button control built using Container."""
    controls = []
    if icon:
        icon_val = getattr(ft.Icons, icon.upper(), icon) if isinstance(icon, str) else icon
        controls.append(ft.Icon(icon_val, size=18, color="onPrimary"))
    controls.append(
        ft.Text(text, weight=ft.FontWeight.W_600, color="onPrimary", size=14)
    )

    return ft.Container(
        content=ft.Row(
            controls=controls,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
            spacing=8,
        ),
        bgcolor="primary",
        padding=pad_symmetric(horizontal=20, vertical=12),
        border_radius=20,
        on_click=on_click,
        ink=True,
    )


class SettingsView(ft.Container):
    """User profile and system settings panel with database persistence."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.app_page = page

        # Input fields
        self.name_input = ft.TextField(label="Student Name", expand=True)
        self.student_id_input = ft.TextField(label="Student ID Number", expand=True)
        self.major_input = ft.TextField(label="Major Program", expand=True)
        self.email_input = ft.TextField(label="Email Address", expand=True)

        # Success notification banner
        icon_check = getattr(ft.Icons, "CHECK_CIRCLE_OUTLINE", "check_circle")
        self.status_banner = ft.Container(
            visible=False,
            padding=12,
            bgcolor="greenContainer",
            border_radius=8,
            content=ft.Row(
                controls=[
                    ft.Icon(icon_check, color="green", size=20),
                    ft.Text(
                        "Student profile saved to database successfully!",
                        color="green",
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                spacing=10,
            ),
        )

        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Manage your personal profile and application configuration", color="secondary"),
                ft.Divider(height=1),
                self.status_banner,
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=20,
                        content=ft.Column(
                            spacing=15,
                            controls=[
                                ft.Text("User Profile Information", size=18, weight=ft.FontWeight.BOLD),
                                ft.ResponsiveRow(
                                    controls=[
                                        ft.Container(col={"xs": 12, "md": 6}, content=self.name_input),
                                        ft.Container(col={"xs": 12, "md": 6}, content=self.student_id_input),
                                    ]
                                ),
                                ft.ResponsiveRow(
                                    controls=[
                                        ft.Container(col={"xs": 12, "md": 6}, content=self.major_input),
                                        ft.Container(col={"xs": 12, "md": 6}, content=self.email_input),
                                    ]
                                ),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                    controls=[
                                        create_primary_button("Save Profile", icon="SAVE", on_click=self._handle_save_profile)
                                    ],
                                ),
                            ],
                        ),
                    ),
                ),
            ],
        )

        self._load_profile_data()

    def _load_profile_data(self) -> None:
        profile = get_student_profile()
        if profile:
            self.name_input.value = profile.name
            self.student_id_input.value = profile.student_id_number
            self.major_input.value = profile.major
            self.email_input.value = profile.email

    def _handle_save_profile(self, e: ft.ControlEvent) -> None:
        name = self.name_input.value.strip() if self.name_input.value else ""
        student_id_val = self.student_id_input.value.strip() if self.student_id_input.value else ""
        major = self.major_input.value.strip() if self.major_input.value else ""
        email = self.email_input.value.strip() if self.email_input.value else ""

        if not name or not student_id_val:
            return

        update_student_profile(
            name=name,
            student_id_number=student_id_val,
            major=major,
            email=email,
        )

        self.status_banner.visible = True
        self.update()
