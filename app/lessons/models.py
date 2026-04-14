"""Lesson data model — defines the structure for all curriculum lessons."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Clef(Enum):
    TREBLE = "treble"
    BASS = "bass"
    GRAND = "grand"


class LessonType(Enum):
    """What kind of lesson this is."""

    READING = "reading"  # informational content + diagrams
    EXERCISE = "exercise"  # interactive play-along exercise


@dataclass(frozen=True)
class Exercise:
    """A single exercise within a lesson.

    Attributes:
        clef: Which clef to display (treble, bass, or grand).
        note_pool: MIDI numbers of notes that may appear in this exercise.
        num_notes: How many notes the student must identify.
        pass_threshold: Fraction correct to pass (default 0.8 = 80%).
        key_signature: Key name (e.g. 'G', 'F', 'Bb') or None for C major.
    """

    clef: Clef
    note_pool: tuple[int, ...]
    num_notes: int = 10
    pass_threshold: float = 0.80
    key_signature: str | None = None


@dataclass(frozen=True)
class Lesson:
    """A single lesson in the curriculum.

    Attributes:
        id: Unique lesson identifier, e.g. "1.1".
        title: Human-readable title.
        level: Curriculum level (1, 2, 3, …).
        description: Short summary shown on the lesson list.
        content_md: Full lesson content in Markdown (rendered on the detail page).
        exercises: Ordered list of exercises that must be completed.
        prerequisite_id: Lesson id that must be completed before this unlocks.
            None means always unlocked.
    """

    id: str
    title: str
    level: int
    description: str
    content_md: str
    exercises: tuple[Exercise, ...] = ()
    prerequisite_id: str | None = None
