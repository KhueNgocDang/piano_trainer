"""Shared page layout — header, left drawer, content area."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from nicegui import ui

from app.midi.bridge import MidiBridge

if TYPE_CHECKING:
    pass

NAV_ITEMS = [
    ("Home", "/", "home"),
    ("Lessons", "/lessons", "menu_book"),
    ("Practice", "/practice", "piano"),
    ("Flash Cards", "/flashcards", "style"),
    ("Progress", "/progress", "bar_chart"),
    ("Settings", "/settings", "settings"),
]


@contextmanager
def create_layout(page_title: str):
    """Create the shared layout and yield the MidiBridge for the page to use.

    Usage::

        with create_layout("Home") as midi:
            ui.label("Page content here")
            # midi is the MidiBridge instance for this client
    """
    # Create the per-client MIDI bridge (hidden element + event handlers)
    midi = MidiBridge()

    # --- Header ---
    with ui.header().classes("items-center justify-between px-4 bg-blue-900"):
        with ui.row().classes("items-center gap-2"):
            menu_btn = ui.button(icon="menu").props(
                "flat dense round color=white"
            )
            ui.label("Piano Trainer").classes("text-xl font-bold text-white")

        with ui.row().classes("items-center gap-3"):
            midi_badge = ui.badge("MIDI: --", color="grey")
            midi_badge.classes("text-sm px-3 py-1")
            midi_device_select = ui.select(
                options={},
                label="MIDI Device",
                value=None,
            ).props(
                'dense outlined dark options-dense style="min-width: 220px"'
            )
            midi_device_select.classes("text-white")

    # --- Left Drawer ---
    with ui.left_drawer(value=True, bordered=True).classes(
        "bg-grey-2"
    ) as drawer:
        ui.label("Navigation").classes(
            "text-subtitle1 font-bold q-mb-sm q-mt-sm q-ml-md"
        )
        for label, route, icon in NAV_ITEMS:
            with ui.item(on_click=lambda r=route: ui.navigate.to(r)).classes(
                "cursor-pointer"
            ):
                with ui.item_section().props("avatar"):
                    ui.icon(icon).classes("text-blue-800")
                with ui.item_section():
                    ui.label(label)
            if label != "Settings":
                ui.separator()

    menu_btn.on_click(drawer.toggle)

    # --- Main Content ---
    with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-4"):
        ui.label(page_title).classes("text-h4 font-bold")

        # Build MIDI log container (initially hidden, toggled by pages that need it)
        log_container = _build_midi_log_panel()

        # Bind the MIDI bridge to UI elements
        midi.bind_ui(midi_badge, midi_device_select, log_container)

        # Inject Web MIDI JS after the bridge element exists
        midi.inject_js()

        yield midi


def _build_midi_log_panel() -> ui.column:
    """Build the MIDI debug log panel and return the log container."""
    with ui.expansion("MIDI Debug Log", icon="terminal").classes("w-full"):
        with (
            ui.scroll_area()
            .classes("w-full h-64 bg-grey-10 rounded p-2")
            .props('id="midi-log-scroll"')
        ):
            log_container = ui.column().classes("w-full gap-0")
    return log_container
