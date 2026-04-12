"""Home page content."""

from nicegui import ui

from app.keyboard.renderer import create_keyboard
from app.midi.bridge import MidiBridge


def content(midi: MidiBridge) -> None:
    """Render the home page."""
    ui.markdown(
        """
Welcome to **Piano Trainer** — your personal sight-reading teacher.

Connect your CASIO Privia (or any MIDI keyboard) and start learning
to read sheet music from scratch.

### Quick Start

1. **Connect your piano** via USB-C MIDI cable.
2. Select your MIDI device from the dropdown in the header.
3. Verify the connection by pressing any key — you'll see it in the MIDI Debug Log below.
4. Head to **Lessons** to begin learning!
"""
    )

    with ui.row().classes("gap-4 q-mt-md"):
        ui.button(
            "Start Lessons",
            icon="menu_book",
            on_click=lambda: ui.navigate.to("/lessons"),
        ).props("size=lg color=primary")
        ui.button(
            "Practice",
            icon="piano",
            on_click=lambda: ui.navigate.to("/practice"),
        ).props("size=lg color=secondary outline")

    ui.separator()
    ui.label("Your Keyboard").classes("text-h6")
    create_keyboard()
