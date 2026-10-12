# src/views/schedule_view.py
import flet as ft
from database.crud import (
    get_schedule_blocks,
    create_schedule_block_by_code,
    update_schedule_block_by_code,
    delete_schedule_block,
)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
ALL_DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def align_center():
    """Cross-version center alignment helper."""
    if hasattr(ft, "Alignment"):
        return ft.Alignment(0, 0)
    return "center"


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
        padding=pad_symmetric(horizontal=16, vertical=10),
        border_radius=20,
        on_click=on_click,
        ink=True,
    )


def create_secondary_button(text: str, on_click=None) -> ft.Container:
    """Version-agnostic secondary text button control built using Container."""
    return ft.Container(
        content=ft.Text(text, weight=ft.FontWeight.W_500, color="primary", size=14),
        padding=pad_symmetric(horizontal=12, vertical=8),
        border_radius=12,
        on_click=on_click,
        ink=True,
    )


def open_dialog_compat(page: ft.Page, dialog: ft.AlertDialog):
    """Safely attaches dialogs to page overlay and displays them across Flet versions."""
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    dialog.open = True
    if hasattr(page, "open") and callable(getattr(page, "open")):
        try:
            page.open(dialog)
        except Exception:
            pass
    page.update()


def close_dialog_compat(page: ft.Page, dialog: ft.AlertDialog):
    """Safely closes dialogs across Flet API revisions."""
    dialog.open = False
    if hasattr(page, "close") and callable(getattr(page, "close")):
        try:
            page.close(dialog)
        except Exception:
            pass
    page.update()


class ScheduleView(ft.Container):
    """Interactive weekly class schedule view rendering daily timeline grids and management dialogs."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.app_page = page

        self.schedule_blocks = []
        self.show_weekends = False
        self.editing_block_id = None

        # Form controls - typable inputs for course details
        self.course_code_input = ft.TextField(
            label="Course Code / Number",
            hint_text="e.g. CS101 / MATH201",
            expand=True,
        )
        self.course_title_input = ft.TextField(
            label="Course Name / Title",
            hint_text="e.g. Intro to Computer Science",
            expand=True,
        )
        self.day_dropdown = ft.Dropdown(
            label="Day of Week",
            expand=True,
            options=[ft.dropdown.Option(day) for day in ALL_DAYS_OF_WEEK],
            value="Monday",
        )
        self.start_time_input = ft.TextField(label="Start Time", value="09:00", expand=True)
        self.end_time_input = ft.TextField(label="End Time", value="10:30", expand=True)
        self.room_input = ft.TextField(label="Room", value="Hall 101", expand=True)
        self.error_text = ft.Text("", color="error", size=12)
        self.dialog_title = ft.Text("Add Class Schedule Block", weight=ft.FontWeight.BOLD)

        self.add_dialog = ft.AlertDialog(
            title=self.dialog_title,
            content=ft.Container(
                width=450,
                content=ft.Column(
                    tight=True,
                    spacing=15,
                    controls=[
                        ft.Row(controls=[self.course_code_input, self.course_title_input], spacing=10),
                        self.day_dropdown,
                        ft.Row(controls=[self.start_time_input, self.end_time_input], spacing=10),
                        self.room_input,
                        self.error_text,
                    ],
                ),
            ),
            actions=[
                create_secondary_button("Cancel", on_click=self._close_dialog),
                create_primary_button("Save Block", on_click=self._handle_save_schedule_block),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.grid_row = ft.ResponsiveRow(spacing=15, run_spacing=15)
        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                self._build_header(),
                ft.Divider(height=1),
                self.grid_row,
            ],
        )

        self._load_data()

    def _build_header(self) -> ft.Row:
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Weekly Schedule", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Interactive weekly timetable and room allocations", color="secondary"),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Switch(
                            label="Show Weekends",
                            value=self.show_weekends,
                            on_change=self._toggle_weekends,
                            tooltip="Toggle Saturday & Sunday schedule columns",
                        ),
                        create_primary_button("Add Class", icon="ADD", on_click=self._open_add_dialog),
                    ],
                    spacing=15,
                ),
            ],
        )

    def _toggle_weekends(self, e: ft.ControlEvent) -> None:
        self.show_weekends = e.control.value
        self._render_schedule_grid()
        self.update()

    def _load_data(self) -> None:
        self.schedule_blocks = get_schedule_blocks()
        self._render_schedule_grid()

    def _render_schedule_grid(self) -> None:
        self.grid_row.controls.clear()
        side_outline = ft.BorderSide(1, "outlineVariant")
        active_days = ALL_DAYS_OF_WEEK if self.show_weekends else WEEKDAYS
        col_span = {"xs": 12, "sm": 6, "md": 1.7} if self.show_weekends else {"xs": 12, "sm": 6, "md": 2.4}

        for day in active_days:
            day_blocks = [b for b in self.schedule_blocks if b.day_of_week == day]
            day_blocks.sort(key=lambda x: x.start_time)

            day_cards = [self._create_block_card(b) for b in day_blocks]
            if not day_cards:
                day_cards.append(
                    ft.Container(
                        padding=15,
                        alignment=align_center(),
                        border=ft.Border(
                            top=side_outline,
                            bottom=side_outline,
                            left=side_outline,
                            right=side_outline,
                        ),
                        border_radius=8,
                        content=ft.Text("No classes", size=12, color="outline"),
                    )
                )

            day_column = ft.Container(
                col=col_span,
                content=ft.Column(
                    controls=[
                        ft.Container(
                            padding=10,
                            bgcolor=getattr(ft.Colors, "SURFACE_CONTAINER_HIGHEST", "surfaceVariant"),
                            border_radius=6,
                            alignment=align_center(),
                            content=ft.Text(day, weight=ft.FontWeight.BOLD),
                        ),
                        ft.Column(controls=day_cards, spacing=10),
                    ],
                    spacing=10,
                ),
            )
            self.grid_row.controls.append(day_column)

    def _create_block_card(self, block) -> ft.Card:
        course_color = block.course.color if block.course else "#2196F3"
        course_title = block.course.title if block.course else "Class Event"
        course_code = block.course.code if block.course else "COURSE"

        icon_edit = getattr(ft.Icons, "EDIT_OUTLINE", getattr(ft.Icons, "EDIT", "edit"))
        icon_delete = getattr(ft.Icons, "DELETE_OUTLINE", getattr(ft.Icons, "DELETE", "delete"))
        icon_schedule = getattr(ft.Icons, "SCHEDULE", "schedule")
        icon_location = getattr(ft.Icons, "LOCATION_ON", "location_on")

        def handle_edit(e, block_item=block):
            self._open_edit_dialog(block_item)

        def handle_delete(e, block_id=block.id):
            self._handle_delete_block(block_id)

        return ft.Card(
            elevation=2,
            content=ft.Container(
                padding=12,
                border_radius=8,
                border=ft.Border(left=ft.BorderSide(6, course_color)),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    expand=True,
                                    controls=[
                                        ft.Text(course_code, weight=ft.FontWeight.BOLD, size=14),
                                        ft.Text(course_title, size=11, color="secondary", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ],
                                ),
                                ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=icon_edit,
                                            icon_size=16,
                                            tooltip="Edit Class",
                                            on_click=handle_edit,
                                        ),
                                        ft.IconButton(
                                            icon=icon_delete,
                                            icon_size=16,
                                            tooltip="Delete Class",
                                            on_click=handle_delete,
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(icon_schedule, size=14, color="primary"),
                                ft.Text(f"{block.start_time} - {block.end_time}", size=11, weight=ft.FontWeight.W_500),
                            ],
                            spacing=4,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(icon_location, size=14, color="secondary"),
                                ft.Text(block.room, size=11, color="secondary"),
                            ],
                            spacing=4,
                        ),
                    ],
                ),
            ),
        )

    def _open_add_dialog(self, e: ft.ControlEvent) -> None:
        self.editing_block_id = None
        self.dialog_title.value = "Add Class Schedule Block"
        self.course_code_input.value = ""
        self.course_title_input.value = ""
        self.day_dropdown.value = "Monday"
        self.start_time_input.value = "09:00"
        self.end_time_input.value = "10:30"
        self.room_input.value = "Hall 101"
        self.error_text.value = ""
        open_dialog_compat(self.app_page, self.add_dialog)

    def _open_edit_dialog(self, block) -> None:
        self.editing_block_id = block.id
        self.dialog_title.value = "Edit Class Schedule Block"
        self.course_code_input.value = str(block.course.code) if block.course else ""
        self.course_title_input.value = str(block.course.title) if block.course else ""
        self.day_dropdown.value = str(block.day_of_week)
        self.start_time_input.value = str(block.start_time)
        self.end_time_input.value = str(block.end_time)
        self.room_input.value = str(block.room)
        self.error_text.value = ""
        open_dialog_compat(self.app_page, self.add_dialog)

    def _close_dialog(self, e: ft.ControlEvent = None) -> None:
        close_dialog_compat(self.app_page, self.add_dialog)

    def _handle_save_schedule_block(self, e: ft.ControlEvent) -> None:
        course_code = self.course_code_input.value.strip().upper() if self.course_code_input.value else ""
        course_title = self.course_title_input.value.strip() if self.course_title_input.value else ""

        if not course_code:
            self.error_text.value = "Enter a course code (e.g., CS101)."
            self.app_page.update()
            return

        day_of_week = self.day_dropdown.value
        start_time = self.start_time_input.value.strip()
        end_time = self.end_time_input.value.strip()
        room = self.room_input.value.strip()

        if self.editing_block_id is None:
            create_schedule_block_by_code(
                course_code=course_code,
                course_title=course_title,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                room=room,
            )
        else:
            update_schedule_block_by_code(
                block_id=self.editing_block_id,
                course_code=course_code,
                course_title=course_title,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                room=room,
            )

        self._close_dialog()
        self._load_data()
        self.update()

    def _handle_delete_block(self, block_id: int) -> None:
        delete_schedule_block(block_id)
        self._load_data()
        self.update()
