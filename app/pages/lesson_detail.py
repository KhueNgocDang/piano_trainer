"""Lesson detail page — shows lesson content and interactive exercises."""

from __future__ import annotations

from nicegui import ui

from app.keyboard.renderer import create_keyboard
from app.lessons.curriculum import LESSON_BY_ID
from app.lessons.db import get_progress, save_attempt
from app.lessons.exercise import LessonExercise
from app.midi.bridge import MidiBridge


async def content(midi: MidiBridge, lesson_id: str) -> None:
    """Render a single lesson's detail page."""
    lesson = LESSON_BY_ID.get(lesson_id)
    if lesson is None:
        ui.label(f"Lesson '{lesson_id}' not found.").classes("text-red-600 text-h6")
        ui.button("Back to Lessons", icon="arrow_back", on_click=lambda: ui.navigate.to("/lessons"))
        return

    progress = await get_progress(lesson_id)

    # Back navigation
    ui.button(
        "← Back to Lessons",
        icon="arrow_back",
        on_click=lambda: ui.navigate.to("/lessons"),
    ).props("flat color=primary")

    # Lesson header
    with ui.row().classes("items-center gap-3 q-my-sm"):
        ui.label(f"Lesson {lesson.id}").classes("text-h5 font-bold")
        if progress and progress.get("completed"):
            ui.badge("Completed", color="green").classes("text-sm")

    # Lesson content (Markdown)
    ui.markdown(lesson.content_md).classes("w-full q-my-md")

    # Exercises
    if lesson.exercises:
        ui.separator()
        for i, exercise in enumerate(lesson.exercises):
            async def _on_complete(score: float, passed: bool, lid=lesson_id):
                await save_attempt(lid, score, passed)
                if passed:
                    ui.notify(
                        "Lesson completed! The next lesson is now unlocked.",
                        type="positive",
                        position="top",
                    )

            ex_ui = LessonExercise(exercise, midi, on_complete=_on_complete)
            ex_ui.create_ui()

    # Keyboard
    ui.separator()
    ui.label("Your Keyboard").classes("text-h6")
    create_keyboard()
