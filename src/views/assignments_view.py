# src/views/assignments_view.py
import datetime
import flet as ft
from database.crud import (
    get_assignments,
    get_courses,
    update_assignment_status,
    create_assignment,
    update_assignment,
    delete_assignment,
)

STATUS_TODO = "Pending"
STATUS_IN_PROGRESS = "In-Progress"
STATUS_DONE = "Done"


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


STATUS_COLUMNS = [
    {
        "key": STATUS_TODO,
        "label": "To-Do",
        "icon": getattr(ft.Icons, "ASSIGNMENT", "assignment"),
        "color": getattr(ft.Colors, "AMBER", "amber"),
    },
    {
        "key": STATUS_IN_PROGRESS,
        "label": "In Progress",
        "icon": getattr(ft.Icons, "AUTORENEW", "autorenew"),
        "color": getattr(ft.Colors, "BLUE", "blue"),
    },
    {
        "key": STATUS_DONE,
        "label": "Submitted",
        "icon": getattr(ft.Icons, "CHECK_CIRCLE", "check_circle"),
        "color": getattr(ft.Colors, "GREEN", "green"),
    },
]


def compute_due_badge(due_date_str: str, status: str):
    icon_task = getattr(ft.Icons, "TASK_ALT", "task_alt")
    icon_warning = getattr(ft.Icons, "WARNING", "warning")
    icon_access = getattr(ft.Icons, "ACCESS_TIME", "access_time")
    icon_calendar = getattr(ft.Icons, "CALENDAR_MONTH", "calendar_month")
    icon_schedule = getattr(ft.Icons, "SCHEDULE", "schedule")

    if status == STATUS_DONE:
        return "green", "greenContainer", icon_task, "Submitted"

    try:
        due_dt = datetime.datetime.strptime(due_date_str.strip(), "%Y-%m-%d")
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        diff_days = (due_dt - today).days

        if diff_days < 0:
            return "red", "redContainer", icon_warning, f"Overdue ({abs(diff_days)}d)"
        elif diff_days == 0:
            return "orange", "orangeContainer", icon_access, "Due Today (<24h)"
        else:
            return "blue", "blueContainer", icon_calendar, f"Due in {diff_days}d"
    except ValueError:
        return "grey", "greyContainer", icon_schedule, due_date_str


class AssignmentsView(ft.Container):
    """Kanban board tracking assignment workflows, priorities, details, and submission links."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.app_page = page

        self.assignments = []
        self.courses = []
        self.editing_assignment_id = None

        # Form controls
        self.title_input = ft.TextField(
            label="Assignment Title",
            hint_text="e.g. Midterm Essay / Lab 3",
            expand=True,
        )
        self.course_dropdown = ft.Dropdown(
            label="Select Course",
            expand=True,
            hint_text="Choose associated course",
        )
        self.due_date_input = ft.TextField(
            label="Due Date (YYYY-MM-DD)",
            hint_text="2026-10-20",
            value=datetime.date.today().strftime("%Y-%m-%d"),
            expand=True,
        )
        self.priority_dropdown = ft.Dropdown(
            label="Priority Level",
            expand=True,
            options=[
                ft.dropdown.Option("High"),
                ft.dropdown.Option("Medium"),
                ft.dropdown.Option("Low"),
            ],
            value="Medium",
        )
        self.notes_input = ft.TextField(
            label="Notes / Coursework Details",
            hint_text="Enter assignment instructions or requirements...",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True,
        )
        self.link_input = ft.TextField(
            label="Submission Link (URL)",
            hint_text="https://canvas.university.edu/courses/...",
            expand=True,
        )
        self.error_text = ft.Text("", color="error", size=12)
        self.dialog_title = ft.Text("Create New Assignment", weight=ft.FontWeight.BOLD)

        self.add_dialog = ft.AlertDialog(
            title=self.dialog_title,
            content=ft.Container(
                width=480,
                content=ft.Column(
                    tight=True,
                    spacing=15,
                    controls=[
                        self.title_input,
                        self.course_dropdown,
                        ft.Row(
                            controls=[self.due_date_input, self.priority_dropdown],
                            spacing=10,
                        ),
                        self.notes_input,
                        self.link_input,
                        self.error_text,
                    ],
                ),
            ),
            actions=[
                create_secondary_button("Cancel", on_click=self._close_dialog),
                create_primary_button("Save Assignment", on_click=self._handle_save_assignment),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.kanban_row = ft.ResponsiveRow(spacing=15, run_spacing=15)
        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                self._build_header(),
                ft.Divider(height=1),
                self.kanban_row,
            ],
        )

        self._load_data()

    def _build_header(self) -> ft.Row:
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Assignment Kanban", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Track coursework status, details, and submission links", color="secondary"),
                    ],
                    spacing=4,
                ),
                create_primary_button("New Assignment", icon="ADD", on_click=self._open_add_dialog),
            ],
        )

    def _load_data(self) -> None:
        self.assignments = get_assignments()
        self.courses = get_courses()
        self._populate_course_dropdown()
        self._render_kanban_board()

    def _populate_course_dropdown(self) -> None:
        self.course_dropdown.options = [
            ft.dropdown.Option(
                key=str(c.id),
                text=f"{c.code} - {c.title}",
            )
            for c in self.courses
        ]
        if self.courses and not self.course_dropdown.value:
            self.course_dropdown.value = str(self.courses[0].id)

    def _render_kanban_board(self) -> None:
        self.kanban_row.controls.clear()
        side_outline = ft.BorderSide(1, "outlineVariant")

        for col_info in STATUS_COLUMNS:
            col_key = col_info["key"]
            col_assignments = [a for a in self.assignments if a.status == col_key]
            cards = [self._create_assignment_card(a) for a in col_assignments]

            if not cards:
                cards.append(
                    ft.Container(
                        padding=20,
                        alignment=align_center(),
                        border=ft.Border(
                            top=side_outline,
                            bottom=side_outline,
                            left=side_outline,
                            right=side_outline,
                        ),
                        border_radius=8,
                        content=ft.Text("No assignments", size=12, color="outline"),
                    )
                )

            column_control = ft.Container(
                col={"xs": 12, "md": 4},
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Container(
                            padding=12,
                            bgcolor=getattr(ft.Colors, "SURFACE_CONTAINER_HIGHEST", "surfaceVariant"),
                            border_radius=8,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Icon(col_info["icon"], color=col_info["color"], size=20),
                                            ft.Text(col_info["label"], weight=ft.FontWeight.BOLD, size=16),
                                        ],
                                        spacing=8,
                                    ),
                                    ft.Container(
                                        padding=pad_symmetric(horizontal=8, vertical=2),
                                        bgcolor="primaryContainer",
                                        border_radius=12,
                                        content=ft.Text(
                                            str(len(col_assignments)),
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color="onPrimaryContainer",
                                        ),
                                    ),
                                ],
                            ),
                        ),
                        ft.Column(controls=cards, spacing=10),
                    ],
                ),
            )
            self.kanban_row.controls.append(column_control)

    def _create_assignment_card(self, assignment) -> ft.Card:
        text_color, bg_color, due_icon, due_text = compute_due_badge(
            assignment.due_date, assignment.status
        )

        course_code = assignment.course.code if assignment.course else "GENERAL"
        course_color = assignment.course.color if assignment.course else "#2196F3"

        icon_back = getattr(ft.Icons, "ARROW_BACK", "arrow_back")
        icon_forward = getattr(ft.Icons, "ARROW_FORWARD", "arrow_forward")
        icon_edit = getattr(ft.Icons, "EDIT_OUTLINE", getattr(ft.Icons, "EDIT", "edit"))
        icon_delete = getattr(ft.Icons, "DELETE_OUTLINE", getattr(ft.Icons, "DELETE", "delete"))
        icon_link = getattr(ft.Icons, "LINK", "link")

        nav_actions = []
        if assignment.status != STATUS_TODO:
            prev_status = STATUS_TODO if assignment.status == STATUS_IN_PROGRESS else STATUS_IN_PROGRESS
            nav_actions.append(
                ft.IconButton(
                    icon=icon_back,
                    icon_size=16,
                    tooltip=f"Move to {prev_status}",
                    on_click=lambda e, a_id=assignment.id, s=prev_status: self._change_status(a_id, s),
                )
            )

        if assignment.status != STATUS_DONE:
            next_status = STATUS_IN_PROGRESS if assignment.status == STATUS_TODO else STATUS_DONE
            nav_actions.append(
                ft.IconButton(
                    icon=icon_forward,
                    icon_size=16,
                    tooltip=f"Move to {next_status}",
                    on_click=lambda e, a_id=assignment.id, s=next_status: self._change_status(a_id, s),
                )
            )

        def handle_edit(e, item=assignment):
            self._open_edit_dialog(item)

        def handle_delete(e, a_id=assignment.id):
            self._handle_delete_assignment(a_id)

        def handle_open_link(e, url=assignment.submission_link):
            if url:
                self.app_page.launch_url(url)

        card_content_controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Container(
                        padding=pad_symmetric(horizontal=6, vertical=2),
                        bgcolor="surfaceVariant",
                        border_radius=4,
                        content=ft.Text(course_code, size=11, weight=ft.FontWeight.BOLD),
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=icon_edit,
                                icon_size=16,
                                tooltip="Edit Assignment",
                                on_click=handle_edit,
                            ),
                            ft.IconButton(
                                icon=icon_delete,
                                icon_size=16,
                                tooltip="Delete Assignment",
                                on_click=handle_delete,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
            ),
            ft.Text(
                assignment.title,
                weight=ft.FontWeight.BOLD,
                size=14,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ]

        # Display assignment notes if present
        if assignment.notes:
            card_content_controls.append(
                ft.Text(
                    assignment.notes,
                    size=12,
                    color="secondary",
                    max_lines=3,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            )

        # Display submission link button if present
        if assignment.submission_link:
            card_content_controls.append(
                ft.Container(
                    padding=pad_symmetric(horizontal=8, vertical=4),
                    bgcolor="surfaceVariant",
                    border_radius=6,
                    on_click=handle_open_link,
                    tooltip="Open Submission Portal",
                    content=ft.Row(
                        controls=[
                            ft.Icon(icon_link, size=14, color="primary"),
                            ft.Text("Submission Link", size=11, color="primary", weight=ft.FontWeight.W_600),
                        ],
                        spacing=6,
                        tight=True,
                    ),
                )
            )

        card_content_controls.extend([
            ft.Container(
                padding=pad_symmetric(horizontal=8, vertical=4),
                bgcolor=bg_color,
                border_radius=6,
                content=ft.Row(
                    controls=[
                        ft.Icon(due_icon, size=14, color=text_color),
                        ft.Text(due_text, size=11, weight=ft.FontWeight.W_600, color=text_color),
                    ],
                    spacing=6,
                    tight=True,
                ),
            ),
            ft.Row(alignment=ft.MainAxisAlignment.END, controls=nav_actions, spacing=0),
        ])

        return ft.Card(
            elevation=2,
            content=ft.Container(
                padding=14,
                border_radius=8,
                border=ft.Border(left=ft.BorderSide(6, course_color)),
                content=ft.Column(spacing=8, controls=card_content_controls),
            ),
        )

    def _change_status(self, assignment_id: int, new_status: str) -> None:
        update_assignment_status(assignment_id, new_status)
        self._load_data()
        self.update()

    def _open_add_dialog(self, e: ft.ControlEvent) -> None:
        self.editing_assignment_id = None
        self.dialog_title.value = "Create New Assignment"
        self.title_input.value = ""
        if self.courses:
            self.course_dropdown.value = str(self.courses[0].id)
        self.due_date_input.value = datetime.date.today().strftime("%Y-%m-%d")
        self.priority_dropdown.value = "Medium"
        self.notes_input.value = ""
        self.link_input.value = ""
        self.error_text.value = ""
        open_dialog_compat(self.app_page, self.add_dialog)

    def _open_edit_dialog(self, assignment) -> None:
        self.editing_assignment_id = assignment.id
        self.dialog_title.value = "Edit Assignment"
        self.title_input.value = str(assignment.title)
        self.course_dropdown.value = str(assignment.course_id)
        self.due_date_input.value = str(assignment.due_date)
        self.priority_dropdown.value = str(assignment.priority)
        self.notes_input.value = str(assignment.notes) if assignment.notes else ""
        self.link_input.value = str(assignment.submission_link) if assignment.submission_link else ""
        self.error_text.value = ""
        open_dialog_compat(self.app_page, self.add_dialog)

    def _close_dialog(self, e: ft.ControlEvent = None) -> None:
        close_dialog_compat(self.app_page, self.add_dialog)

    def _handle_save_assignment(self, e: ft.ControlEvent) -> None:
        title = self.title_input.value.strip() if self.title_input.value else ""
        if not title or not self.course_dropdown.value:
            self.error_text.value = "Please fill in the title and select a course."
            self.app_page.update()
            return

        course_id = int(self.course_dropdown.value)
        due_date = self.due_date_input.value.strip()
        priority = self.priority_dropdown.value
        notes = self.notes_input.value.strip() if self.notes_input.value else None
        link = self.link_input.value.strip() if self.link_input.value else None

        if self.editing_assignment_id is None:
            create_assignment(
                title=title,
                course_id=course_id,
                due_date=due_date,
                priority=priority,
                notes=notes,
                submission_link=link,
            )
        else:
            update_assignment(
                assignment_id=self.editing_assignment_id,
                title=title,
                course_id=course_id,
                due_date=due_date,
                priority=priority,
                notes=notes,
                submission_link=link,
            )

        self._close_dialog()
        self._load_data()
        self.update()

    def _handle_delete_assignment(self, assignment_id: int) -> None:
        delete_assignment(assignment_id)
        self._load_data()
        self.update()
