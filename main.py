#!/usr/bin/env python3
"""Piano Training — Sight-Reading Trainer.

Run with: uv run python main.py
"""

from nicegui import ui

from app.layout import create_layout
from app.pages import home, lessons, practice, flashcards, progress, settings
from app.pages import lesson_detail


@ui.page("/")
def page_home():
    with create_layout("Home") as midi:
        home.content(midi)


@ui.page("/lessons")
async def page_lessons():
    with create_layout("Lessons") as midi:
        await lessons.content(midi)


@ui.page("/lessons/{lesson_id}")
async def page_lesson_detail(lesson_id: str):
    with create_layout("Lesson") as midi:
        await lesson_detail.content(midi, lesson_id)


@ui.page("/practice")
def page_practice():
    with create_layout("Practice") as midi:
        practice.content(midi)


@ui.page("/flashcards")
def page_flashcards():
    with create_layout("Flash Cards") as midi:
        flashcards.content(midi)


@ui.page("/progress")
def page_progress():
    with create_layout("Progress") as midi:
        progress.content(midi)


@ui.page("/settings")
def page_settings():
    with create_layout("Settings") as midi:
        settings.content(midi)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Piano Trainer", port=8080, reload=True)
