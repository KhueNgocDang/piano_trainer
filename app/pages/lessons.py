"""Lessons page — placeholder for Milestone 1."""

from nicegui import ui

from app.midi.bridge import MidiBridge


def content(midi: MidiBridge) -> None:
    ui.label("Lessons will be available in a future milestone.").classes(
        "text-grey-7"
    )
    with ui.card().classes("w-full p-4 bg-grey-2"):
        ui.label("Level 1: The Staff & Clefs").classes("text-h6")
        ui.label("Coming soon...").classes("text-grey-5")
