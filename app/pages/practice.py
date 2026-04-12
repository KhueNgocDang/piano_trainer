"""Practice page — interactive keyboard and note-reading drill."""

from nicegui import ui

from app.keyboard.renderer import create_keyboard
from app.midi.bridge import MidiBridge
from app.staff.drill import NoteDrill


def content(midi: MidiBridge) -> None:
    ui.markdown(
        "Play your piano and watch the keys light up. "
        "Start the **Note Reading Drill** to practice sight-reading on the treble clef."
    )

    drill = NoteDrill(midi)
    drill.create_ui()

    ui.separator()
    ui.label("Your Keyboard").classes("text-h6")
    create_keyboard()
