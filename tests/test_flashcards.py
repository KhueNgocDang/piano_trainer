"""Tests for the Flash Cards module."""

import pytest

from app.pages.flashcards import (
    CLEF_RANGES,
    DEFAULT_CARD_COUNT,
    DEFAULT_CLEF,
    DEFAULT_MODE,
    DEFAULT_TIMER,
    MODE_NAME_TO_PIANO,
    MODE_PIANO_TO_NAME,
    MODE_STAFF_TO_PIANO,
    FlashCardSession,
    _build_note_pool,
    _normalize_note_name,
)
from app.keyboard.renderer import is_black_key


# ── _build_note_pool tests ────────────────────────────────────────


class TestBuildNotePool:
    def test_treble_range(self):
        pool = _build_note_pool("treble", include_sharps=False)
        lo, hi = CLEF_RANGES["treble"]
        assert all(lo <= n <= hi for n in pool)
        assert all(not is_black_key(n) for n in pool)
        assert len(pool) >= 5

    def test_bass_range(self):
        pool = _build_note_pool("bass", include_sharps=False)
        lo, hi = CLEF_RANGES["bass"]
        assert all(lo <= n <= hi for n in pool)

    def test_grand_range(self):
        pool = _build_note_pool("grand", include_sharps=False)
        lo, hi = CLEF_RANGES["grand"]
        assert all(lo <= n <= hi for n in pool)
        assert len(pool) > len(
            _build_note_pool("treble", include_sharps=False)
        )

    def test_include_sharps(self):
        pool_no = _build_note_pool("treble", include_sharps=False)
        pool_yes = _build_note_pool("treble", include_sharps=True)
        assert len(pool_yes) > len(pool_no)

    def test_no_sharps_excludes_black_keys(self):
        pool = _build_note_pool("treble", include_sharps=False)
        for m in pool:
            assert not is_black_key(m), f"MIDI {m} is a black key"

    def test_with_sharps_includes_black_keys(self):
        pool = _build_note_pool("treble", include_sharps=True)
        has_black = any(is_black_key(m) for m in pool)
        assert has_black


# ── _normalize_note_name tests ────────────────────────────────────


class TestNormalizeNoteName:
    def test_lowercase(self):
        assert _normalize_note_name("c4") == "C4"

    def test_uppercase(self):
        assert _normalize_note_name("C4") == "C4"

    def test_sharp(self):
        assert _normalize_note_name("c#4") == "C#4"
        assert _normalize_note_name("C#4") == "C#4"

    def test_flat_to_sharp(self):
        assert _normalize_note_name("Db4") == "C#4"
        assert _normalize_note_name("Eb4") == "D#4"
        assert _normalize_note_name("Gb3") == "F#3"
        assert _normalize_note_name("Ab3") == "G#3"
        assert _normalize_note_name("Bb3") == "A#3"

    def test_whitespace(self):
        assert _normalize_note_name("  C4  ") == "C4"

    def test_empty(self):
        assert _normalize_note_name("") == ""
        assert _normalize_note_name("   ") == ""


# ── FlashCardSession tests ────────────────────────────────────────


class TestFlashCardSession:
    def _make_session(self, **kwargs):
        s = FlashCardSession()
        s.note_pool = list(range(60, 73))  # C4–C5 naturals+accidentals
        for k, v in kwargs.items():
            setattr(s, k, v)
        return s

    def test_defaults(self):
        s = FlashCardSession()
        assert s.mode == DEFAULT_MODE
        assert s.clef == DEFAULT_CLEF
        assert s.card_limit == DEFAULT_CARD_COUNT
        assert s.timer_seconds == DEFAULT_TIMER
        assert s.hits == 0
        assert s.misses == 0
        assert s.total == 0
        assert s.accuracy == 0.0

    def test_pick_next_returns_from_pool(self):
        s = self._make_session()
        for _ in range(20):
            note = s.pick_next()
            assert note in s.note_pool

    def test_pick_next_increments_card_index(self):
        s = self._make_session()
        assert s.card_index == 0
        s.pick_next()
        assert s.card_index == 1
        s.pick_next()
        assert s.card_index == 2

    def test_pick_next_avoids_recent(self):
        s = self._make_session(note_pool=[60, 62, 64, 65, 67])
        targets = set()
        for _ in range(20):
            t = s.pick_next()
            targets.add(t)
        # Should use multiple different notes
        assert len(targets) > 1

    def test_record_hit(self):
        s = self._make_session()
        s.card_start_time = 100.0
        s.record_hit()
        assert s.hits == 1
        assert len(s.response_times) == 1

    def test_record_miss(self):
        s = self._make_session()
        s.card_start_time = 100.0
        s.record_miss()
        assert s.misses == 1
        assert len(s.response_times) == 1

    def test_accuracy(self):
        s = self._make_session()
        s.hits = 7
        s.misses = 3
        assert s.total == 10
        assert abs(s.accuracy - 0.7) < 0.01

    def test_accuracy_zero_total(self):
        s = self._make_session()
        assert s.accuracy == 0.0

    def test_is_set_complete_with_limit(self):
        s = self._make_session(card_limit=10, card_index=9)
        assert not s.is_set_complete()
        s.card_index = 10
        assert s.is_set_complete()

    def test_is_set_complete_unlimited(self):
        s = self._make_session(card_limit=0, card_index=999)
        assert not s.is_set_complete()

    def test_choose_clef_treble(self):
        s = self._make_session(clef="treble")
        assert s.choose_clef_for_note(60) == "treble"
        assert s.choose_clef_for_note(40) == "treble"

    def test_choose_clef_bass(self):
        s = self._make_session(clef="bass")
        assert s.choose_clef_for_note(60) == "bass"

    def test_choose_clef_grand(self):
        s = self._make_session(clef="grand")
        assert s.choose_clef_for_note(60) == "treble"  # C4 → treble
        assert s.choose_clef_for_note(59) == "bass"  # B3 → bass

    def test_fastest_slowest(self):
        s = self._make_session()
        s.response_times = [1.5, 0.8, 3.2, 2.0]
        assert abs(s.fastest - 0.8) < 0.01
        assert abs(s.slowest - 3.2) < 0.01

    def test_fastest_slowest_empty(self):
        s = self._make_session()
        assert s.fastest == 0.0
        assert s.slowest == 0.0


# ── NiceGUI integration tests ────────────────────────────────────

from nicegui.testing import User


async def test_flashcards_page_loads(user: User):
    await user.open("/flashcards")
    await user.should_see("Flash Cards")
    await user.should_see("Configuration")


async def test_flashcards_page_has_mode_selector(user: User):
    await user.open("/flashcards")
    await user.should_see("Mode")


async def test_flashcards_page_has_clef_selector(user: User):
    await user.open("/flashcards")
    await user.should_see("Clef")


async def test_flashcards_page_has_timer_option(user: User):
    await user.open("/flashcards")
    await user.should_see("Timer per card")


async def test_flashcards_page_has_card_count(user: User):
    await user.open("/flashcards")
    await user.should_see("Card count")


async def test_flashcards_page_has_start_button(user: User):
    await user.open("/flashcards")
    await user.should_see("Start")


async def test_flashcards_page_has_keyboard(user: User):
    await user.open("/flashcards")
    await user.should_see("Your Keyboard")


async def test_flashcards_page_has_score_display(user: User):
    await user.open("/flashcards")
    await user.should_see("Correct: 0 | Wrong: 0")
    await user.should_see("Accuracy: 0%")
