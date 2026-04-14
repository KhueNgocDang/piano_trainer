"""Tests for the Practice page — session state, note pool builder, and page integration."""

from __future__ import annotations

import pytest

from app.keyboard.renderer import is_black_key
from app.pages.practice import (
    CLEF_RANGES,
    DEFAULT_CLEF,
    DEFAULT_LEDGER_LINES,
    DEFAULT_MAX_MIDI,
    DEFAULT_MIN_MIDI,
    DEFAULT_SHARPS_FLATS,
    PracticeSession,
    _build_note_pool,
)


# ═══════════════════════════════════════════════════════════════════
# Note pool builder
# ═══════════════════════════════════════════════════════════════════


class TestBuildNotePool:
    def test_treble_default_no_sharps(self):
        pool = _build_note_pool("treble", 60, 81, include_sharps=False)
        assert all(not is_black_key(m) for m in pool)
        assert 60 in pool  # C4
        assert 81 in pool  # A5

    def test_treble_with_sharps(self):
        pool = _build_note_pool("treble", 60, 72, include_sharps=True)
        has_black = any(is_black_key(m) for m in pool)
        assert has_black

    def test_bass_range(self):
        pool = _build_note_pool("bass", 40, 60, include_sharps=False)
        assert all(not is_black_key(m) for m in pool)
        assert 40 in pool  # E2
        assert 60 in pool  # C4

    def test_empty_range(self):
        pool = _build_note_pool("treble", 60, 60, include_sharps=False)
        assert len(pool) == 1
        assert pool == (60,)

    def test_pool_is_tuple(self):
        pool = _build_note_pool("treble", 60, 72, include_sharps=False)
        assert isinstance(pool, tuple)

    def test_grand_range(self):
        pool = _build_note_pool("grand", 40, 81, include_sharps=False)
        assert len(pool) > 20  # should be many notes
        assert 40 in pool
        assert 81 in pool


# ═══════════════════════════════════════════════════════════════════
# Practice session state
# ═══════════════════════════════════════════════════════════════════


class TestPracticeSession:
    def test_initial_state(self):
        s = PracticeSession()
        assert s.hits == 0
        assert s.misses == 0
        assert s.streak == 0
        assert s.best_streak == 0
        assert s.total == 0
        assert s.accuracy == 0.0

    def test_pick_next_from_pool(self):
        s = PracticeSession(note_pool=[60, 62, 64])
        note = s.pick_next()
        assert note in [60, 62, 64]
        assert s.target_midi == note

    def test_pick_next_avoids_repeats(self):
        s = PracticeSession(note_pool=[60, 62, 64, 65, 67])
        notes = [s.pick_next() for _ in range(20)]
        # No 4 in a row
        for i in range(len(notes) - 3):
            assert not (
                notes[i] == notes[i + 1] == notes[i + 2] == notes[i + 3]
            )

    def test_recent_targets_capped(self):
        s = PracticeSession(note_pool=[60, 62, 64])
        for _ in range(15):
            s.pick_next()
        assert len(s.recent_targets) <= 10

    def test_accuracy(self):
        s = PracticeSession()
        s.hits = 8
        s.misses = 2
        assert s.accuracy == 0.8

    def test_accuracy_zero_when_empty(self):
        s = PracticeSession()
        assert s.accuracy == 0.0

    def test_total(self):
        s = PracticeSession()
        s.hits = 5
        s.misses = 3
        assert s.total == 8

    def test_choose_clef_treble(self):
        s = PracticeSession(clef="treble")
        assert s.choose_clef_for_note(60) == "treble"
        assert s.choose_clef_for_note(40) == "treble"

    def test_choose_clef_bass(self):
        s = PracticeSession(clef="bass")
        assert s.choose_clef_for_note(60) == "bass"

    def test_choose_clef_grand(self):
        s = PracticeSession(clef="grand")
        assert s.choose_clef_for_note(60) == "treble"  # C4 = treble
        assert s.choose_clef_for_note(59) == "bass"  # B3 = bass
        assert s.choose_clef_for_note(72) == "treble"  # C5 = treble
        assert s.choose_clef_for_note(40) == "bass"  # E2 = bass

    def test_streak_tracking(self):
        s = PracticeSession()
        s.hits = 5
        s.streak = 5
        s.best_streak = 5
        # Simulate a miss
        s.misses = 1
        s.streak = 0
        assert s.best_streak == 5  # best preserved
        assert s.streak == 0


# ═══════════════════════════════════════════════════════════════════
# Clef ranges
# ═══════════════════════════════════════════════════════════════════


class TestClefRanges:
    def test_treble_range(self):
        lo, hi = CLEF_RANGES["treble"]
        assert lo == 59  # B3
        assert hi == 81  # A5

    def test_bass_range(self):
        lo, hi = CLEF_RANGES["bass"]
        assert lo == 40  # E2
        assert hi == 60  # C4

    def test_grand_range(self):
        lo, hi = CLEF_RANGES["grand"]
        assert lo == 40  # E2
        assert hi == 81  # A5

    def test_defaults(self):
        assert DEFAULT_CLEF == "treble"
        assert DEFAULT_MIN_MIDI == 60
        assert DEFAULT_MAX_MIDI == 81
        assert DEFAULT_SHARPS_FLATS is False
        assert DEFAULT_LEDGER_LINES is True


# ═══════════════════════════════════════════════════════════════════
# Page integration tests (via NiceGUI User fixture)
# ═══════════════════════════════════════════════════════════════════

from nicegui.testing import User


async def test_practice_page_loads(user: User):
    await user.open("/practice")
    await user.should_see("Practice")


async def test_practice_page_has_config(user: User):
    await user.open("/practice")
    await user.should_see("Configuration")
    await user.should_see("Clef")


async def test_practice_page_has_start_button(user: User):
    await user.open("/practice")
    await user.should_see("Start Practice")


async def test_practice_page_has_scoring(user: User):
    await user.open("/practice")
    await user.should_see("Hits: 0 | Misses: 0")
    await user.should_see("Accuracy: 0%")
    await user.should_see("Streak: 0")


async def test_practice_page_has_keyboard(user: User):
    await user.open("/practice")
    await user.should_see("Your Keyboard")


async def test_practice_page_has_staff(user: User):
    await user.open("/practice")
    await user.should_see("Sight-Reading Practice")


async def test_practice_page_has_options(user: User):
    await user.open("/practice")
    await user.should_see("Include sharps/flats")
    await user.should_see("Include ledger lines")
