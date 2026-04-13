"""Lessons page — shows curriculum with locked/unlocked lesson cards."""

from __future__ import annotations

from itertools import groupby

from nicegui import ui

from app.keyboard.renderer import create_keyboard
from app.lessons.curriculum import ALL_LESSONS, LESSON_BY_ID
from app.lessons.db import get_all_progress, save_attempt
from app.lessons.exercise import LessonExercise
from app.lessons.models import Lesson
from app.midi.bridge import MidiBridge

_LEVEL_TITLES = {
    0: "Level 0 — The Piano Keyboard",
    1: "Level 1 — The Staff & Clefs",
    2: "Level 2 — Note Identification (Treble Clef)",
    3: "Level 3 — Note Identification (Bass Clef)",
}


async def content(midi: MidiBridge) -> None:
    """Render the lessons list page."""
    progress = await get_all_progress()

    ui.markdown(
        "Work through each lesson in order. Complete exercises with "
        "≥80% accuracy to unlock the next lesson."
    )

    for level, lessons in groupby(ALL_LESSONS, key=lambda l: l.level):
        title = _LEVEL_TITLES.get(level, f"Level {level}")
        ui.label(title).classes("text-h5 font-bold q-mt-lg q-mb-sm")

        for lesson in lessons:
            unlocked = _is_unlocked(lesson, progress)
            completed = progress.get(lesson.id, {}).get("completed", False)
            best = progress.get(lesson.id, {}).get("best_score", 0.0)
            attempts = progress.get(lesson.id, {}).get("attempts", 0)

            with ui.card().classes(
                "w-full p-4 "
                + ("bg-white" if unlocked else "bg-grey-3 opacity-70")
            ):
                with ui.row().classes("items-center justify-between w-full"):
                    with ui.row().classes("items-center gap-3"):
                        if completed:
                            ui.icon("check_circle", color="green").classes(
                                "text-2xl"
                            )
                        elif unlocked:
                            ui.icon(
                                "radio_button_unchecked", color="blue"
                            ).classes("text-2xl")
                        else:
                            ui.icon("lock", color="grey").classes("text-2xl")

                        with ui.column().classes("gap-0"):
                            ui.label(
                                f"Lesson {lesson.id}: {lesson.title}"
                            ).classes(
                                "text-h6 " + ("" if unlocked else "text-grey-5")
                            )
                            ui.label(lesson.description).classes(
                                "text-body2 text-grey-7"
                            )
                            if attempts > 0:
                                ui.label(
                                    f"Best: {int(best * 100)}% • {attempts} attempt(s)"
                                ).classes("text-caption text-grey-5")

                    if unlocked:
                        ui.button(
                            "Start" if not completed else "Review",
                            icon="play_arrow" if not completed else "replay",
                            on_click=lambda lid=lesson.id: ui.navigate.to(
                                f"/lessons/{lid}"
                            ),
                        ).props(
                            "color=primary"
                            if not completed
                            else "color=green outline"
                        )


def _is_unlocked(lesson: Lesson, progress: dict) -> bool:
    """A lesson is unlocked if it has no prerequisite, or its prerequisite is completed."""
    if lesson.prerequisite_id is None:
        return True
    prereq = progress.get(lesson.prerequisite_id)
    return prereq is not None and prereq.get("completed", False)
