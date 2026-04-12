"""Settings page — placeholder for Milestone 1."""

from nicegui import ui

from app.midi.bridge import MidiBridge


def content(midi: MidiBridge) -> None:
    ui.label("Settings will be available in a future milestone.").classes(
        "text-grey-7"
    )
