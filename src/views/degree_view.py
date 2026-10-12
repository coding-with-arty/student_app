# src/views/degree_view.py
import os
import flet as ft
from database.crud import (
    get_degree_requirements,
    get_courses,
    get_student_profile,
    update_degree_settings,
    update_degree_requirement,
    update_degree_requirement_status,
    create_degree_requirement,
    delete_degree_requirement,
)

STATUS_COMPLETED = "Completed"
STATUS_IN_PROGRESS = "In-Progress"
STATUS_PLANNED = "Planned"


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


def create_popup_item(text: str, on_click=None) -> ft.PopupMenuItem:
    """Version-agnostic PopupMenuItem helper supporting Flet 0.20+ and 1.0+."""
    try:
        return ft.PopupMenuItem(content=ft.Text(text), on_click=on_click)
    except TypeError:
        return ft.PopupMenuItem(text=text, on_click=on_click)


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


class DegreeView(ft.Container):
    """Visual degree pathway tracker showing prerequisite dependencies, credit progress, and catalog contract locks."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.app_page = page

        self.requirements = []
        self.courses_by_code = {}
        self.editing_req_id = None
        self.total_credits_required = 120
        self.degree_contract_path = None

        # File picker for uploading degree enrollment contract initialized lazily
        self.file_picker = ft.FilePicker(on_result=self._handle_file_picked)

        # Requirement Form controls
        self.course_code_input = ft.TextField(label="Course Code", hint_text="CS201", expand=True)
        self.prereq_code_input = ft.TextField(label="Prerequisite Code", hint_text="CS101", expand=True)
        self.req_error_text = ft.Text("", color="error", size=12)
        self.req_dialog_title = ft.Text("Add Degree Requirement", weight=ft.FontWeight.BOLD)

        self.add_dialog = ft.AlertDialog(
            title=self.req_dialog_title,
            content=ft.Container(
                width=400,
                content=ft.Column(
                    tight=True,
                    spacing=15,
                    controls=[self.course_code_input, self.prereq_code_input, self.req_error_text],
                ),
            ),
            actions=[
                create_secondary_button("Cancel", on_click=self._close_req_dialog),
                create_primary_button("Save", on_click=self._handle_save_requirement),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Degree Settings Form Controls
        self.total_credits_input = ft.TextField(
            label="Total Credits Required for Graduation",
            value="120",
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )
        self.contract_file_text = ft.Text(
            "No contract file uploaded",
            size=12,
            color="secondary",
            weight=ft.FontWeight.W_500,
        )
        self.settings_error_text = ft.Text("", color="error", size=12)

        icon_upload = getattr(ft.Icons, "UPLOAD_FILE", "upload_file")
        self.settings_dialog = ft.AlertDialog(
            title=ft.Text("Degree Program & Contract Settings", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=450,
                content=ft.Column(
                    tight=True,
                    spacing=15,
                    controls=[
                        ft.Text(
                            "Configure your total degree credits and attach your enrollment day degree contract to protect against catalog revisions.",
                            size=12,
                            color="secondary",
                        ),
                        self.total_credits_input,
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Text("Enrollment Degree Contract Document", weight=ft.FontWeight.BOLD, size=13),
                                ft.Row(
                                    controls=[
                                        create_secondary_button("Select Contract File", on_click=self._pick_contract_file),
                                        ft.Icon(icon_upload, size=18, color="primary"),
                                    ],
                                    spacing=8,
                                ),
                                self.contract_file_text,
                            ],
                        ),
                        self.settings_error_text,
                    ],
                ),
            ),
            actions=[
                create_secondary_button("Cancel", on_click=self._close_settings_dialog),
                create_primary_button("Save Settings", on_click=self._handle_save_degree_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.metrics_container = ft.Container()
        self.roadmap_grid = ft.ResponsiveRow(spacing=15, run_spacing=15)

        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                self._build_header(),
                ft.Divider(height=1),
                self.metrics_container,
                ft.Text("Requirements Map", size=20, weight=ft.FontWeight.BOLD),
                self.roadmap_grid,
            ],
        )

        self._load_data()

    def _build_header(self) -> ft.Row:
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Degree Pathway", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Audit prerequisites, credit targets, and enrollment contracts", color="secondary"),
                    ]
                ),
                ft.Row(
                    controls=[
                        create_secondary_button("Edit Goal & Contract", on_click=self._open_settings_dialog),
                        create_primary_button("Add Requirement", icon="ADD", on_click=self._open_add_dialog),
                    ],
                    spacing=10,
                ),
            ],
        )

    def _load_data(self) -> None:
        profile = get_student_profile()
        if profile:
            self.total_credits_required = profile.total_credits_required or 120
            self.degree_contract_path = profile.degree_contract_path

        self.requirements = get_degree_requirements()
        courses = get_courses()
        self.courses_by_code = {c.code.upper(): c for c in courses}
        self._render_metrics()
        self._render_roadmap_grid()

    def _is_prereq_satisfied(self, req) -> bool:
        if not req.prerequisite_code:
            return True
        prereq = req.prerequisite_code.strip().upper()
        completed = {r.course_code.strip().upper() for r in self.requirements if r.status == STATUS_COMPLETED}
        return prereq in completed

    def _render_metrics(self) -> None:
        completed = [r for r in self.requirements if r.status == STATUS_COMPLETED]
        earned_credits = sum(
            self.courses_by_code[r.course_code.upper()].credits
            if r.course_code.upper() in self.courses_by_code
            else 3
            for r in completed
        )
        total_credits = self.total_credits_required if self.total_credits_required > 0 else 120
        ratio = min(1.0, earned_credits / total_credits)

        icon_edit = getattr(ft.Icons, "EDIT_OUTLINE", getattr(ft.Icons, "EDIT", "edit"))
        icon_verified = getattr(ft.Icons, "VERIFIED_USER", "verified")
        icon_link = getattr(ft.Icons, "ATTACH_FILE", "attach_file")

        contract_widgets = []
        if self.degree_contract_path:
            filename = os.path.basename(self.degree_contract_path)

            def open_contract(e):
                if self.degree_contract_path:
                    self.app_page.launch_url(f"file://{self.degree_contract_path}")

            contract_widgets.append(
                ft.Container(
                    padding=pad_symmetric(horizontal=10, vertical=6),
                    bgcolor="surfaceVariant",
                    border_radius=6,
                    on_click=open_contract,
                    tooltip="Open Enrollment Contract",
                    content=ft.Row(
                        controls=[
                            ft.Icon(icon_verified, size=16, color="green"),
                            ft.Text(f"Contract: {filename}", size=12, weight=ft.FontWeight.W_600, color="green"),
                            ft.Icon(icon_link, size=14, color="primary"),
                        ],
                        spacing=6,
                        tight=True,
                    ),
                )
            )
        else:
            contract_widgets.append(
                ft.Text("No degree contract uploaded on enrollment day.", size=12, color="outline")
            )

        self.metrics_container.content = ft.Card(
            elevation=2,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    f"Graduation Progress ({earned_credits} / {total_credits} Credits Required)",
                                    weight=ft.FontWeight.BOLD,
                                    size=16,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text(f"{int(ratio * 100)}%", weight=ft.FontWeight.BOLD, color="primary", size=16),
                                        ft.IconButton(
                                            icon=icon_edit,
                                            icon_size=16,
                                            tooltip="Edit Total Credits Target",
                                            on_click=self._open_settings_dialog,
                                        ),
                                    ],
                                    spacing=4,
                                ),
                            ],
                        ),
                        ft.ProgressBar(value=ratio, color="primary", height=8),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=contract_widgets,
                        ),
                    ],
                ),
            ),
        )

    def _render_roadmap_grid(self) -> None:
        self.roadmap_grid.controls.clear()

        icon_check = getattr(ft.Icons, "CHECK_CIRCLE", "check_circle")
        icon_auto = getattr(ft.Icons, "AUTORENEW", "autorenew")
        icon_lock = getattr(ft.Icons, "LOCK", "lock")
        icon_schedule = getattr(ft.Icons, "SCHEDULE", "schedule")
        icon_more = getattr(ft.Icons, "MORE_VERT", "more_vert")
        icon_edit = getattr(ft.Icons, "EDIT_OUTLINE", getattr(ft.Icons, "EDIT", "edit"))
        icon_delete = getattr(ft.Icons, "DELETE_OUTLINE", getattr(ft.Icons, "DELETE", "delete"))

        for req in self.requirements:
            prereq_met = self._is_prereq_satisfied(req)

            if req.status == STATUS_COMPLETED:
                badge_bg, badge_fg, icon, label = "greenContainer", "green", icon_check, "Completed"
            elif req.status == STATUS_IN_PROGRESS:
                badge_bg, badge_fg, icon, label = "blueContainer", "blue", icon_auto, "In Progress"
            elif not prereq_met:
                badge_bg, badge_fg, icon, label = "greyContainer", "grey", icon_lock, f"Locked ({req.prerequisite_code})"
            else:
                badge_bg, badge_fg, icon, label = "amberContainer", "amber", icon_schedule, "Planned"

            def handle_edit(e, req_item=req):
                self._open_edit_dialog(req_item)

            def handle_delete(e, req_id=req.id):
                self._delete_req(req_id)

            card = ft.Card(
                elevation=2,
                col={"xs": 12, "sm": 6, "md": 4},
                content=ft.Container(
                    padding=15,
                    border_radius=8,
                    border=ft.Border(left=ft.BorderSide(6, badge_fg)),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text(req.course_code.upper(), weight=ft.FontWeight.BOLD, size=16),
                            ft.Container(
                                padding=pad_symmetric(horizontal=8, vertical=4),
                                bgcolor=badge_bg,
                                border_radius=6,
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(icon, size=14, color=badge_fg),
                                        ft.Text(label, size=11, color=badge_fg, weight=ft.FontWeight.W_600),
                                    ],
                                    spacing=6,
                                ),
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.PopupMenuButton(
                                        icon=icon_more,
                                        items=[
                                            create_popup_item(
                                                "Completed",
                                                on_click=lambda e, r_id=req.id: self._update_status(r_id, STATUS_COMPLETED),
                                            ),
                                            create_popup_item(
                                                "In-Progress",
                                                on_click=lambda e, r_id=req.id: self._update_status(r_id, STATUS_IN_PROGRESS),
                                            ),
                                            create_popup_item(
                                                "Planned",
                                                on_click=lambda e, r_id=req.id: self._update_status(r_id, STATUS_PLANNED),
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.IconButton(
                                                icon=icon_edit,
                                                icon_size=16,
                                                tooltip="Edit Requirement",
                                                on_click=handle_edit,
                                            ),
                                            ft.IconButton(
                                                icon=icon_delete,
                                                icon_size=16,
                                                tooltip="Delete Requirement",
                                                on_click=handle_delete,
                                            ),
                                        ],
                                        spacing=0,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            )
            self.roadmap_grid.controls.append(card)

    def _update_status(self, req_id: int, status: str) -> None:
        update_degree_requirement_status(req_id, status)
        self._load_data()
        self.update()

    def _delete_req(self, req_id: int) -> None:
        delete_degree_requirement(req_id)
        self._load_data()
        self.update()

    def _open_add_dialog(self, e: ft.ControlEvent) -> None:
        self.editing_req_id = None
        self.req_dialog_title.value = "Add Degree Requirement"
        self.course_code_input.value = ""
        self.prereq_code_input.value = ""
        self.req_error_text.value = ""
        open_dialog_compat(self.app_page, self.add_dialog)

    def _open_edit_dialog(self, req) -> None:
        self.editing_req_id = req.id
        self.req_dialog_title.value = "Edit Degree Requirement"
        self.course_code_input.value = str(req.course_code)
        self.prereq_code_input.value = str(req.prerequisite_code) if req.prerequisite_code else ""
        self.req_error_text.value = ""
        open_dialog_compat(self.app_page, self.add_dialog)

    def _close_req_dialog(self, e: ft.ControlEvent = None) -> None:
        close_dialog_compat(self.app_page, self.add_dialog)

    def _handle_save_requirement(self, e: ft.ControlEvent) -> None:
        code = self.course_code_input.value.strip().upper() if self.course_code_input.value else ""
        if not code:
            self.req_error_text.value = "Please enter a course code."
            self.app_page.update()
            return

        prereq = self.prereq_code_input.value.strip().upper() if self.prereq_code_input.value else None

        if self.editing_req_id is None:
            create_degree_requirement(course_code=code, prerequisite_code=prereq)
        else:
            update_degree_requirement(req_id=self.editing_req_id, course_code=code, prerequisite_code=prereq)

        self._close_req_dialog()
        self._load_data()
        self.update()

    def _open_settings_dialog(self, e: ft.ControlEvent) -> None:
        self.total_credits_input.value = str(self.total_credits_required)
        if self.degree_contract_path:
            self.contract_file_text.value = f"Current file: {os.path.basename(self.degree_contract_path)}"
        else:
            self.contract_file_text.value = "No contract document selected"
        self.settings_error_text.value = ""
        open_dialog_compat(self.app_page, self.settings_dialog)

    def _close_settings_dialog(self, e: ft.ControlEvent = None) -> None:
        close_dialog_compat(self.app_page, self.settings_dialog)

    def _pick_contract_file(self, e: ft.ControlEvent) -> None:
        # Safely bind FilePicker to page overlay at runtime right before invocation
        if self.file_picker not in self.app_page.overlay:
            self.app_page.overlay.append(self.file_picker)
            self.app_page.update()

        self.file_picker.pick_files(
            dialog_title="Select Degree Enrollment Contract",
            allow_multiple=False,
            allowed_extensions=["pdf", "doc", "docx", "png", "jpg"],
        )

    def _handle_file_picked(self, e: ft.FilePickerResultEvent) -> None:
        if e.files and len(e.files) > 0:
            picked_path = e.files[0].path or e.files[0].name
            self.degree_contract_path = picked_path
            self.contract_file_text.value = f"Selected: {os.path.basename(picked_path)}"
            if hasattr(self.settings_dialog, "update") and callable(getattr(self.settings_dialog, "update")):
                try:
                    self.settings_dialog.update()
                except Exception:
                    pass
            self.app_page.update()

    def _handle_save_degree_settings(self, e: ft.ControlEvent) -> None:
        try:
            val = int(self.total_credits_input.value.strip())
            if val <= 0:
                raise ValueError()
            self.total_credits_required = val
        except Exception:
            self.settings_error_text.value = "Enter a valid positive total credits number."
            self.app_page.update()
            return

        update_degree_settings(
            total_credits=self.total_credits_required,
            contract_path=self.degree_contract_path,
        )

        self._close_settings_dialog()
        self._load_data()
        self.update()
