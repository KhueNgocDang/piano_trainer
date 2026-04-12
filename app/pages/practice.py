"""Practice page — interactive keyboard for free play."""

from nicegui import ui

from app.keyboard.renderer import create_keyboard
from app.midi.bridge import MidiBridge


def content(midi: MidiBridge) -> None:
    ui.markdown(
        "Play your piano and watch the keys light up below. "
        "Structured practice exercises will be added in a future milestone."
    )
    create_keyboard()
