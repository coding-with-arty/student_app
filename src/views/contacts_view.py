# src/views/contacts_view.py
import os
import shutil
import uuid
import flet as ft
from database.crud import (
    get_contacts,
    create_contact,
    update_contact,
    delete_contact,
)
from utils.theme import pad_symmetric, align_center

# Absolute path resolutions for local uploads folder
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(THIS_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
UPLOAD_DIR = os.path.join(ASSETS_DIR, "uploads", "contacts")


def open_dialog_compat(page: ft.Page, dialog: ft.AlertDialog):
    """Safely displays dialogs using mutually exclusive branching to prevent duplicate overlay crashes."""
    if hasattr(page, "open") and callable(getattr(page, "open")):
        page.open(dialog)
    else:
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()


def close_dialog_compat(page: ft.Page, dialog: ft.AlertDialog):
    """Safely closes dialogs across Flet API revisions."""
    if hasattr(page, "close") and callable(getattr(page, "close")):
        page.close(dialog)
    else:
        dialog.open = False
        page.update()


def show_snackbar(page: ft.Page, message: str):
    """Displays a temporary feedback notification banner."""
    snack = ft.SnackBar(content=ft.Text(message, color="onPrimary"), bgcolor="primary", open=True)
    if hasattr(page, "open") and callable(getattr(page, "open")):
        try:
            page.open(snack)
            return
        except Exception:
            pass
    page.snack_bar = snack
    snack.open = True
    page.update()


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


class ContactsView(ft.Container):
    """School directory view utilizing shared page FilePicker for thumbnail photo uploads."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.app_page = page

        self.contacts = []
        self.filtered_contacts = []
        self.editing_contact_id = None
        self.selected_image_path = None

        # Ensure destination uploads directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Form Controls
        self.name_input = ft.TextField(label="Full Name*", expand=True)
        self.email_input = ft.TextField(label="Email Address", expand=True)
        self.phone_input = ft.TextField(label="Phone Number", expand=True)
        self.address_input = ft.TextField(label="Address / Office Location", expand=True)
        self.links_input = ft.TextField(label="Links / Portal URL", hint_text="https://...", expand=True)
        self.notes_input = ft.TextField(
            label="Notes & Details",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
        )
        self.error_text = ft.Text("", color="error", size=12)
        self.photo_status_text = ft.Text("", size=11, weight=ft.FontWeight.W_600)

        # Search Control
        self.search_input = ft.TextField(
            hint_text="Search contacts by name, email, or notes...",
            prefix_icon=getattr(ft.Icons, "SEARCH", "search"),
            expand=True,
            on_change=self._handle_search,
        )

        # Modal Avatar Preview Container
        self.modal_avatar_container = ft.Container(
            width=110,
            height=110,
            border_radius=55,
            bgcolor="surfaceVariant",
            alignment=align_center(),
        )

        self.dialog_title = ft.Text("Contact Details", weight=ft.FontWeight.BOLD)

        cross_align_start = getattr(ft.CrossAxisAlignment, "START", "start")
        cross_align_center = getattr(ft.CrossAxisAlignment, "CENTER", "center")

        # Modal Edit / Add Dialog Layout
        self.contact_dialog = ft.AlertDialog(
            title=self.dialog_title,
            content=ft.Container(
                width=580,
                content=ft.Column(
                    tight=True,
                    spacing=15,
                    controls=[
                        ft.Row(
                            vertical_alignment=cross_align_start,
                            spacing=20,
                            controls=[
                                # Image Preview Column
                                ft.Column(
                                    horizontal_alignment=cross_align_center,
                                    spacing=8,
                                    width=130,
                                    controls=[
                                        self.modal_avatar_container,
                                        create_secondary_button(
                                            "Upload Photo", on_click=self._pick_image_file
                                        ),
                                        self.photo_status_text,
                                    ],
                                ),
                                # Input Controls Column
                                ft.Column(
                                    expand=True,
                                    spacing=12,
                                    controls=[
                                        self.name_input,
                                        ft.Row(
                                            controls=[self.email_input, self.phone_input],
                                            spacing=10,
                                        ),
                                        self.address_input,
                                        self.links_input,
                                        self.notes_input,
                                        self.error_text,
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            actions=[
                create_secondary_button("Cancel", on_click=self._close_dialog),
                create_primary_button("Save Contact", on_click=self._handle_save_contact),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.list_container = ft.Column(spacing=10)
        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                self._build_header(),
                ft.Divider(height=1),
                ft.Row(controls=[self.search_input]),
                self.list_container,
            ],
        )

        self._load_data()

    def _get_file_picker(self) -> ft.FilePicker:
        """Retrieves or instantiates global FilePicker service attached to Page."""
        fp = getattr(self.app_page, "file_picker", None)
        if not fp:
            fp = ft.FilePicker()
            self.app_page.file_picker = fp

        if hasattr(self.app_page, "open") and callable(getattr(self.app_page, "open")):
            try:
                self.app_page.open(fp)
            except Exception:
                pass

        return fp

    def _build_header(self) -> ft.Row:
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("School Contacts & Address Book", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Directory of professors, advisors, and academic departments", color="secondary"),
                    ]
                ),
                create_primary_button("Add Contact", icon="PERSON_ADD", on_click=self._open_add_dialog),
            ],
        )

    def _load_data(self) -> None:
        try:
            self.contacts = get_contacts()
            self.filtered_contacts = list(self.contacts)
        except Exception:
            self.contacts = []
            self.filtered_contacts = []
        self._render_contact_list()

    def _handle_search(self, e: ft.ControlEvent) -> None:
        query = self.search_input.value.strip().lower() if self.search_input.value else ""
        if not query:
            self.filtered_contacts = list(self.contacts)
        else:
            self.filtered_contacts = [
                c for c in self.contacts
                if query in c.name.lower()
                or (c.email and query in c.email.lower())
                or (c.notes and query in c.notes.lower())
                or (c.address and query in c.address.lower())
            ]
        self._render_contact_list()
        self.update()

    def _copy_image_to_uploads(self, source_path: str) -> str:
        """Copies source file into assets/uploads/contacts/ and returns relative asset path."""
        if not source_path:
            return source_path

        abs_source = os.path.abspath(source_path)
        if not os.path.exists(abs_source):
            return source_path

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        abs_upload = os.path.abspath(UPLOAD_DIR)

        # Avoid re-copying if image is already inside upload directory
        if abs_source.startswith(abs_upload):
            filename = os.path.basename(abs_source)
            return f"/uploads/contacts/{filename}"

        file_ext = os.path.splitext(source_path)[1].lower() or ".png"
        unique_filename = f"contact_{uuid.uuid4().hex[:10]}{file_ext}"
        destination_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            shutil.copy2(abs_source, destination_path)
        except Exception:
            return source_path

        return f"/uploads/contacts/{unique_filename}"

    def _create_avatar_control(self, name: str, image_path: str = None, radius: int = 24) -> ft.Control:
        """Generates thumbnail controls: ft.Image using relative asset path if valid file exists on disk."""
        initial = name[0].upper() if name and len(name) > 0 else "?"
        size_dim = radius * 2

        if image_path and isinstance(image_path, str) and len(image_path.strip()) > 0:
            clean_rel = "/" + image_path.lstrip("/\\").replace("\\", "/")
            disk_rel = clean_rel.lstrip("/")
            full_disk_path = os.path.normpath(os.path.join(ASSETS_DIR, disk_rel))

            if os.path.exists(full_disk_path) or os.path.exists(image_path):
                img_fit = getattr(ft.ImageFit, "COVER", "cover")
                clip_hard = getattr(ft.ClipBehavior, "HARD_EDGE", "hardEdge")

                return ft.Container(
                    width=size_dim,
                    height=size_dim,
                    border_radius=radius,
                    clip_behavior=clip_hard,
                    content=ft.Image(
                        src=clean_rel,
                        width=size_dim,
                        height=size_dim,
                        fit=img_fit,
                        error_content=ft.CircleAvatar(
                            content=ft.Text(initial, weight=ft.FontWeight.BOLD, size=max(10, radius - 2), color="onPrimaryContainer"),
                            bgcolor="primaryContainer",
                            radius=radius,
                        ),
                    ),
                )

        return ft.CircleAvatar(
            content=ft.Text(initial, weight=ft.FontWeight.BOLD, size=max(10, radius - 2), color="onPrimaryContainer"),
            bgcolor="primaryContainer",
            radius=radius,
        )

    def _render_contact_list(self) -> None:
        self.list_container.controls.clear()

        if not self.filtered_contacts:
            self.list_container.controls.append(
                ft.Container(
                    padding=30,
                    alignment=align_center(),
                    content=ft.Text("No contacts found", color="outline", size=14),
                )
            )
            return

        icon_email = getattr(ft.Icons, "EMAIL", "email")
        icon_phone = getattr(ft.Icons, "PHONE", "phone")
        icon_location = getattr(ft.Icons, "LOCATION_ON", "location_on")
        icon_link = getattr(ft.Icons, "LINK", "link")
        icon_edit = getattr(ft.Icons, "EDIT_OUTLINE", getattr(ft.Icons, "EDIT", "edit"))
        icon_delete = getattr(ft.Icons, "DELETE_OUTLINE", getattr(ft.Icons, "DELETE", "delete"))

        cross_align_center = getattr(ft.CrossAxisAlignment, "CENTER", "center")

        for contact in self.filtered_contacts:
            def handle_click_view(e, item=contact):
                self._open_edit_dialog(item)

            def handle_delete(e, item_id=contact.id):
                self._handle_delete_contact(item_id)

            def handle_open_link(e, url=contact.links):
                if url:
                    self.app_page.launch_url(url)

            sub_info = []
            if contact.email:
                sub_info.append(
                    ft.Row(
                        controls=[
                            ft.Icon(icon_email, size=13, color="secondary"),
                            ft.Text(contact.email, size=12, color="secondary"),
                        ],
                        spacing=4,
                        tight=True,
                    )
                )
            if contact.phone:
                sub_info.append(
                    ft.Row(
                        controls=[
                            ft.Icon(icon_phone, size=13, color="secondary"),
                            ft.Text(contact.phone, size=12, color="secondary"),
                        ],
                        spacing=4,
                        tight=True,
                    )
                )
            if contact.address:
                sub_info.append(
                    ft.Row(
                        controls=[
                            ft.Icon(icon_location, size=13, color="secondary"),
                            ft.Text(contact.address, size=12, color="secondary"),
                        ],
                        spacing=4,
                        tight=True,
                    )
                )

            card_content = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=cross_align_center,
                controls=[
                    ft.Row(
                        spacing=15,
                        expand=True,
                        controls=[
                            self._create_avatar_control(contact.name, contact.image_path, radius=24),
                            ft.Column(
                                spacing=4,
                                expand=True,
                                controls=[
                                    ft.Text(contact.name, weight=ft.FontWeight.BOLD, size=16),
                                    ft.Row(controls=sub_info, spacing=12, run_spacing=4, wrap=True),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.IconButton(
                                icon=icon_link,
                                icon_size=18,
                                tooltip="Open Link",
                                visible=bool(contact.links),
                                on_click=handle_open_link,
                            ),
                            ft.IconButton(
                                icon=icon_edit,
                                icon_size=18,
                                tooltip="View / Edit Contact",
                                on_click=handle_click_view,
                            ),
                            ft.IconButton(
                                icon=icon_delete,
                                icon_size=18,
                                tooltip="Delete Contact",
                                on_click=handle_delete,
                            ),
                        ],
                    ),
                ],
            )

            card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=14,
                    border_radius=8,
                    on_click=handle_click_view,
                    content=card_content,
                ),
            )
            self.list_container.controls.append(card)

    def _update_modal_avatar_preview(self) -> None:
        """Updates modal avatar preview with uploaded image or default initial."""
        current_name = self.name_input.value.strip() if self.name_input.value else "New Contact"
        self.modal_avatar_container.content = self._create_avatar_control(
            current_name, self.selected_image_path, radius=50
        )
        if self.selected_image_path:
            filename = os.path.basename(self.selected_image_path)
            self.photo_status_text.value = f"✓ Attached:\n{filename[:16]}"
            self.photo_status_text.color = "green"
        else:
            self.photo_status_text.value = ""

    def _open_add_dialog(self, e: ft.ControlEvent) -> None:
        self.editing_contact_id = None
        self.selected_image_path = None
        self.dialog_title.value = "Add New Contact"
        self.name_input.value = ""
        self.email_input.value = ""
        self.phone_input.value = ""
        self.address_input.value = ""
        self.links_input.value = ""
        self.notes_input.value = ""
        self.error_text.value = ""
        self._update_modal_avatar_preview()
        open_dialog_compat(self.app_page, self.contact_dialog)

    def _open_edit_dialog(self, contact) -> None:
        self.editing_contact_id = contact.id
        self.selected_image_path = contact.image_path
        self.dialog_title.value = f"Contact Details: {contact.name}"
        self.name_input.value = str(contact.name or "")
        self.email_input.value = str(contact.email or "")
        self.phone_input.value = str(contact.phone or "")
        self.address_input.value = str(contact.address or "")
        self.links_input.value = str(contact.links or "")
        self.notes_input.value = str(contact.notes or "")
        self.error_text.value = ""
        self._update_modal_avatar_preview()
        open_dialog_compat(self.app_page, self.contact_dialog)

    def _close_dialog(self, e: ft.ControlEvent = None) -> None:
        close_dialog_compat(self.app_page, self.contact_dialog)

    def _pick_image_file(self, e: ft.ControlEvent) -> None:
        """Triggers FilePicker registered on page session."""
        fp = self._get_file_picker()
        fp.on_result = self._handle_file_picked

        try:
            fp.pick_files(
                dialog_title="Select Contact Photo",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
            )
        except Exception as ex:
            self.error_text.value = f"Unable to open file picker: {str(ex)}"
            self.app_page.update()

    def _handle_file_picked(self, e: ft.FilePickerResultEvent) -> None:
        """Event callback triggered when user selects a file in the OS dialog."""
        if not e or not hasattr(e, "files") or not e.files or len(e.files) == 0:
            return

        file_item = e.files[0]
        picked_path = getattr(file_item, "path", None) or getattr(file_item, "name", None)

        if picked_path:
            rel_asset_path = self._copy_image_to_uploads(picked_path)
            self.selected_image_path = rel_asset_path
            self._update_modal_avatar_preview()
            try:
                self.contact_dialog.update()
            except Exception:
                pass
            self.app_page.update()

    def _handle_save_contact(self, e: ft.ControlEvent) -> None:
        name = self.name_input.value.strip() if self.name_input.value else ""
        if not name:
            self.error_text.value = "Full Name is required."
            self.app_page.update()
            return

        email = self.email_input.value.strip() if self.email_input.value else None
        phone = self.phone_input.value.strip() if self.phone_input.value else None
        address = self.address_input.value.strip() if self.address_input.value else None
        links = self.links_input.value.strip() if self.links_input.value else None
        notes = self.notes_input.value.strip() if self.notes_input.value else None

        if self.editing_contact_id is None:
            create_contact(
                name=name,
                email=email,
                phone=phone,
                address=address,
                links=links,
                notes=notes,
                image_path=self.selected_image_path,
            )
            action_msg = f"Contact '{name}' saved successfully!"
        else:
            update_contact(
                contact_id=self.editing_contact_id,
                name=name,
                email=email,
                phone=phone,
                address=address,
                links=links,
                notes=notes,
                image_path=self.selected_image_path,
            )
            action_msg = f"Contact '{name}' updated successfully!"

        self._close_dialog()
        self._load_data()
        self.update()
        show_snackbar(self.app_page, action_msg)

    def _handle_delete_contact(self, contact_id: int) -> None:
        delete_contact(contact_id)
        self._load_data()
        self.update()
        show_snackbar(self.app_page, "Contact deleted successfully!")
