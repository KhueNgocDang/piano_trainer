"""Tests for lesson models, curriculum, database, exercise engine, and staff renderers (bass/grand)."""

from __future__ import annotations

import asyncio
import os
import tempfile

import pytest

from app.keyboard.renderer import is_black_key
from app.lessons.models import Clef, Exercise, Lesson, LessonType
from app.lessons.curriculum import (
    ALL_LESSONS,
    LESSON_0_1,
    LESSON_0_2,
    LESSON_0_3,
    LESSON_1_1,
    LESSON_1_2,
    LESSON_1_3,
    LESSON_1_4,
    LESSON_2_1,
    LESSON_2_2,
    LESSON_2_3,
    LESSON_2_4,
    LESSON_2_5,
    LESSON_3_1,
    LESSON_3_2,
    LESSON_3_3,
    LESSON_3_4,
    LESSON_3_5,
    LESSON_4_1,
    LESSON_4_2,
    LESSON_BY_ID,
    LEVEL_0_LESSONS,
    LEVEL_1_LESSONS,
    LEVEL_2_LESSONS,
    LEVEL_3_LESSONS,
    LEVEL_4_LESSONS,
)
from app.lessons import db as lesson_db
from app.lessons.exercise import ExerciseState, FLASH_JS
from app.staff.renderer import (
    midi_to_bass_staff_y,
    midi_to_staff_y,
    midi_to_grand_staff_y,
    needs_ledger_lines_bass,
    needs_ledger_lines_grand,
    render_bass_staff_svg,
    render_grand_staff_svg,
    render_staff_svg,
    LINE_SPACING,
    STAFF_TOP,
    GRAND_TREBLE_TOP,
    GRAND_BASS_TOP,
    GRAND_STAFF_HEIGHT,
)


# ═══════════════════════════════════════════════════════════════════
# Lesson Models
# ═══════════════════════════════════════════════════════════════════


class TestLessonModels:
    def test_clef_enum(self):
        assert Clef.TREBLE.value == "treble"
        assert Clef.BASS.value == "bass"
        assert Clef.GRAND.value == "grand"

    def test_exercise_defaults(self):
        ex = Exercise(clef=Clef.TREBLE, note_pool=(60, 62, 64))
        assert ex.num_notes == 10
        assert ex.pass_threshold == 0.80

    def test_exercise_custom(self):
        ex = Exercise(
            clef=Clef.BASS,
            note_pool=(43, 45),
            num_notes=5,
            pass_threshold=0.70,
        )
        assert ex.num_notes == 5
        assert ex.pass_threshold == 0.70

    def test_lesson_fields(self):
        lesson = Lesson(
            id="test.1",
            title="Test",
            level=1,
            description="A test lesson",
            content_md="# Test",
        )
        assert lesson.id == "test.1"
        assert lesson.prerequisite_id is None
        assert lesson.exercises == ()

    def test_lesson_frozen(self):
        lesson = LESSON_1_1
        with pytest.raises(AttributeError):
            lesson.title = "changed"


# ═══════════════════════════════════════════════════════════════════
# Curriculum
# ═══════════════════════════════════════════════════════════════════


class TestCurriculum:
    def test_all_lessons_count(self):
        assert len(ALL_LESSONS) == 19  # 3 + 4 + 5 + 5 + 2

    def test_all_levels_make_all(self):
        assert (
            ALL_LESSONS
            == LEVEL_0_LESSONS
            + LEVEL_1_LESSONS
            + LEVEL_2_LESSONS
            + LEVEL_3_LESSONS
            + LEVEL_4_LESSONS
        )

    def test_lesson_ids_unique(self):
        ids = [l.id for l in ALL_LESSONS]
        assert len(ids) == len(set(ids))

    def test_lesson_by_id(self):
        assert LESSON_BY_ID["0.1"] is LESSON_0_1
        assert LESSON_BY_ID["1.1"] is LESSON_1_1
        assert LESSON_BY_ID["1.4"] is LESSON_1_4
        assert LESSON_BY_ID["2.1"] is LESSON_2_1
        assert LESSON_BY_ID["3.5"] is LESSON_3_5
        assert LESSON_BY_ID["4.1"] is LESSON_4_1
        assert LESSON_BY_ID["4.2"] is LESSON_4_2

    def test_lesson_0_1_unlocked(self):
        assert LESSON_0_1.prerequisite_id is None

    def test_level_0_prerequisite_chain(self):
        assert LESSON_0_2.prerequisite_id == "0.1"
        assert LESSON_0_3.prerequisite_id == "0.2"

    def test_level_1_requires_level_0(self):
        assert LESSON_1_1.prerequisite_id == "0.3"

    def test_level_1_prerequisite_chain(self):
        assert LESSON_1_2.prerequisite_id == "1.1"
        assert LESSON_1_3.prerequisite_id == "1.2"
        assert LESSON_1_4.prerequisite_id == "1.3"

    def test_all_lessons_have_exercises(self):
        for lesson in ALL_LESSONS:
            assert len(lesson.exercises) >= 1

    def test_level_0_lessons_have_content(self):
        for lesson in LEVEL_0_LESSONS:
            assert len(lesson.content_md) > 50
            assert lesson.level == 0

    def test_lesson_0_1_center_keys(self):
        ex = LESSON_0_1.exercises[0]
        # C4, D4, E4, F4, G4
        assert set(ex.note_pool) == {60, 62, 64, 65, 67}

    def test_lesson_0_2_one_octave(self):
        ex = LESSON_0_2.exercises[0]
        # C4–B4 (7 white keys)
        assert len(ex.note_pool) == 7
        assert ex.note_pool[0] == 60  # C4
        assert ex.note_pool[-1] == 71  # B4

    def test_lesson_0_3_two_octaves(self):
        ex = LESSON_0_3.exercises[0]
        # C3–B4 (14 white keys)
        assert len(ex.note_pool) == 14
        for m in ex.note_pool:
            assert not is_black_key(m)

    def test_lesson_1_1_treble_lines(self):
        ex = LESSON_1_1.exercises[0]
        assert ex.clef == Clef.TREBLE
        # E4, G4, B4, D5, F5
        assert set(ex.note_pool) == {64, 67, 71, 74, 77}

    def test_lesson_1_3_bass(self):
        ex = LESSON_1_3.exercises[0]
        assert ex.clef == Clef.BASS
        for m in ex.note_pool:
            assert not is_black_key(m)

    def test_lesson_1_4_grand_staff(self):
        ex = LESSON_1_4.exercises[0]
        assert ex.clef == Clef.GRAND
        # Should include both treble and bass notes
        has_treble = any(m >= 64 for m in ex.note_pool)
        has_bass = any(m < 60 for m in ex.note_pool)
        assert has_treble
        assert has_bass

    # ── Level 2 — Treble Clef Note Identification ────────────────

    def test_level_2_count(self):
        assert len(LEVEL_2_LESSONS) == 5

    def test_level_2_all_treble(self):
        for lesson in LEVEL_2_LESSONS:
            assert lesson.level == 2
            for ex in lesson.exercises:
                assert ex.clef == Clef.TREBLE

    def test_level_2_prerequisite_chain(self):
        assert LESSON_2_1.prerequisite_id == "1.4"
        assert LESSON_2_2.prerequisite_id == "2.1"
        assert LESSON_2_3.prerequisite_id == "2.2"
        assert LESSON_2_4.prerequisite_id == "2.3"
        assert LESSON_2_5.prerequisite_id == "2.4"

    def test_level_2_progressive_pools(self):
        """Each lesson's note pool should be a superset of the previous."""
        pools = [set(l.exercises[0].note_pool) for l in LEVEL_2_LESSONS]
        for i in range(1, len(pools)):
            assert pools[i - 1].issubset(
                pools[i]
            ), f"Lesson 2.{i} pool is not a superset of 2.{i - 1}"

    def test_lesson_2_1_notes(self):
        ex = LESSON_2_1.exercises[0]
        assert set(ex.note_pool) == {60, 62, 64}  # C4, D4, E4

    def test_lesson_2_3_octave(self):
        ex = LESSON_2_3.exercises[0]
        assert set(ex.note_pool) == {60, 62, 64, 65, 67, 69, 71, 72}

    def test_lesson_2_4_includes_ledger_notes(self):
        ex = LESSON_2_4.exercises[0]
        pool = set(ex.note_pool)
        assert 59 in pool  # B3 below staff
        assert 77 in pool  # F5 top line

    def test_lesson_2_5_full_range(self):
        ex = LESSON_2_5.exercises[0]
        pool = set(ex.note_pool)
        assert 59 in pool  # B3
        assert 81 in pool  # A5
        assert len(pool) == 14
        for m in pool:
            assert not is_black_key(m)

    def test_level_2_content(self):
        for lesson in LEVEL_2_LESSONS:
            assert len(lesson.content_md) > 50

    # ── Level 3 — Bass Clef Note Identification ──────────────────

    def test_level_3_count(self):
        assert len(LEVEL_3_LESSONS) == 5

    def test_level_3_all_bass(self):
        for lesson in LEVEL_3_LESSONS:
            assert lesson.level == 3
            for ex in lesson.exercises:
                assert ex.clef == Clef.BASS

    def test_level_3_prerequisite_chain(self):
        assert LESSON_3_1.prerequisite_id == "2.5"
        assert LESSON_3_2.prerequisite_id == "3.1"
        assert LESSON_3_3.prerequisite_id == "3.2"
        assert LESSON_3_4.prerequisite_id == "3.3"
        assert LESSON_3_5.prerequisite_id == "3.4"

    def test_level_3_progressive_pools(self):
        """Each lesson's note pool should be a superset of the previous."""
        pools = [set(l.exercises[0].note_pool) for l in LEVEL_3_LESSONS]
        for i in range(1, len(pools)):
            assert pools[i - 1].issubset(
                pools[i]
            ), f"Lesson 3.{i} pool is not a superset of 3.{i - 1}"

    def test_lesson_3_1_notes(self):
        ex = LESSON_3_1.exercises[0]
        assert set(ex.note_pool) == {57, 59, 60}  # A3, B3, C4

    def test_lesson_3_3_center(self):
        ex = LESSON_3_3.exercises[0]
        pool = set(ex.note_pool)
        assert 48 in pool  # C3
        assert 60 in pool  # C4

    def test_lesson_3_4_includes_bottom(self):
        ex = LESSON_3_4.exercises[0]
        pool = set(ex.note_pool)
        assert 43 in pool  # G2 (line 1)
        assert 41 in pool  # F2 (below staff)

    def test_lesson_3_5_full_range(self):
        ex = LESSON_3_5.exercises[0]
        pool = set(ex.note_pool)
        assert 40 in pool  # E2
        assert 60 in pool  # C4
        assert len(pool) == 13
        for m in pool:
            assert not is_black_key(m)

    def test_level_3_content(self):
        for lesson in LEVEL_3_LESSONS:
            assert len(lesson.content_md) > 50

    # ── Level 4 — Both Clefs Together ─────────────────────────────

    def test_level_4_count(self):
        assert len(LEVEL_4_LESSONS) == 2

    def test_level_4_all_grand(self):
        for lesson in LEVEL_4_LESSONS:
            assert lesson.level == 4
            for ex in lesson.exercises:
                assert ex.clef == Clef.GRAND

    def test_level_4_prerequisite_chain(self):
        assert LESSON_4_1.prerequisite_id == "3.5"
        assert LESSON_4_2.prerequisite_id == "4.1"

    def test_lesson_4_1_grand_staff_pool(self):
        ex = LESSON_4_1.exercises[0]
        pool = set(ex.note_pool)
        # Should include both treble and bass notes
        has_treble = any(m >= 64 for m in pool)
        has_bass = any(m < 55 for m in pool)
        assert has_treble, "Lesson 4.1 should include treble range notes"
        assert has_bass, "Lesson 4.1 should include bass range notes"
        # Should include notes from both L2 and L3 ranges
        assert 60 in pool  # Middle C
        assert 40 in pool or 41 in pool  # Low bass notes

    def test_lesson_4_1_no_duplicates(self):
        ex = LESSON_4_1.exercises[0]
        assert len(ex.note_pool) == len(set(ex.note_pool))

    def test_lesson_4_2_landmarks(self):
        ex = LESSON_4_2.exercises[0]
        pool = set(ex.note_pool)
        assert 60 in pool  # Middle C (C4)
        assert 41 in pool  # F2 (bass landmark)
        assert 79 in pool  # G5 (treble landmark)
        assert len(pool) == 3

    def test_level_4_content(self):
        for lesson in LEVEL_4_LESSONS:
            assert len(lesson.content_md) > 50

    # ── Full prerequisite chain ───────────────────────────────────

    def test_full_prerequisite_chain(self):
        """Every lesson except 0.1 has a prerequisite that exists."""
        for lesson in ALL_LESSONS:
            if lesson.prerequisite_id is not None:
                assert (
                    lesson.prerequisite_id in LESSON_BY_ID
                ), f"Lesson {lesson.id} has invalid prerequisite {lesson.prerequisite_id}"

    def test_no_black_keys_in_note_pools(self):
        for lesson in ALL_LESSONS:
            for ex in lesson.exercises:
                for m in ex.note_pool:
                    assert not is_black_key(m), f"Black key {m} in {lesson.id}"

    def test_all_lessons_have_content(self):
        for lesson in ALL_LESSONS:
            assert len(lesson.content_md) > 50


# ═══════════════════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    """Use a temporary directory for the database."""
    monkeypatch.setattr(lesson_db, "_DB_DIR", tmp_path)
    monkeypatch.setattr(lesson_db, "_DB_PATH", tmp_path / "progress.db")
    return tmp_path


class TestDatabase:
    @pytest.mark.asyncio
    async def test_get_progress_empty(self, tmp_db):
        result = await lesson_db.get_progress("1.1")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get(self, tmp_db):
        await lesson_db.save_attempt("1.1", 0.90, True)
        result = await lesson_db.get_progress("1.1")
        assert result is not None
        assert result["lesson_id"] == "1.1"
        assert result["best_score"] == 0.90
        assert result["attempts"] == 1
        assert result["completed"] is True

    @pytest.mark.asyncio
    async def test_multiple_attempts_keeps_best(self, tmp_db):
        await lesson_db.save_attempt("1.1", 0.60, False)
        await lesson_db.save_attempt("1.1", 0.90, True)
        await lesson_db.save_attempt(
            "1.1", 0.70, False
        )  # lower score, already completed
        result = await lesson_db.get_progress("1.1")
        assert result["best_score"] == 0.90
        assert result["attempts"] == 3
        assert result["completed"] is True  # stays True once achieved

    @pytest.mark.asyncio
    async def test_get_all_progress(self, tmp_db):
        await lesson_db.save_attempt("1.1", 0.85, True)
        await lesson_db.save_attempt("1.2", 0.50, False)
        all_prog = await lesson_db.get_all_progress()
        assert "1.1" in all_prog
        assert "1.2" in all_prog
        assert all_prog["1.1"]["completed"] is True
        assert all_prog["1.2"]["completed"] is False

    @pytest.mark.asyncio
    async def test_reset_progress(self, tmp_db):
        await lesson_db.save_attempt("1.1", 0.90, True)
        await lesson_db.reset_progress()
        result = await lesson_db.get_progress("1.1")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# Bass Clef Renderer
# ═══════════════════════════════════════════════════════════════════


class TestBassClefRenderer:
    def test_d3_on_line_3(self):
        """D3 (MIDI 50) should be on line 3 of the bass clef."""
        y = midi_to_bass_staff_y(50)
        expected = STAFF_TOP + 2 * LINE_SPACING  # line 3 from top
        assert y == expected

    def test_g2_on_line_1(self):
        """G2 (MIDI 43) on line 1 (bottom)."""
        y = midi_to_bass_staff_y(43)
        expected = STAFF_TOP + 4 * LINE_SPACING
        assert y is not None
        assert abs(y - expected) < 0.5

    def test_a3_on_line_5(self):
        """A3 (MIDI 57) on line 5 (top)."""
        y = midi_to_bass_staff_y(57)
        expected = STAFF_TOP + 0 * LINE_SPACING
        assert y is not None
        assert abs(y - expected) < 0.5

    def test_accidental_returns_none(self):
        assert midi_to_bass_staff_y(61) is None  # C#4

    def test_higher_notes_lower_y(self):
        y_g2 = midi_to_bass_staff_y(43)
        y_a3 = midi_to_bass_staff_y(57)
        assert y_g2 > y_a3  # lower note = higher y

    def test_c4_needs_ledger_above(self):
        """C4 (MIDI 60) is above the bass staff — needs ledger line."""
        ledgers = needs_ledger_lines_bass(60)
        assert len(ledgers) >= 1

    def test_e2_needs_ledger_below(self):
        """E2 (MIDI 40) is below the bass staff — needs ledger line."""
        ledgers = needs_ledger_lines_bass(40)
        assert len(ledgers) >= 1

    def test_d3_on_staff_no_ledger(self):
        """D3 on line 3 — no ledger lines needed."""
        ledgers = needs_ledger_lines_bass(50)
        assert ledgers == []

    def test_render_empty_bass_staff(self):
        svg = render_bass_staff_svg()
        assert "bass-staff" in svg
        assert "<line" in svg
        assert "bass-staff-note" not in svg

    def test_render_bass_staff_with_note(self):
        svg = render_bass_staff_svg(target_midi=50)
        assert "bass-staff-note" in svg
        assert "ellipse" in svg

    def test_bass_clef_symbol(self):
        svg = render_bass_staff_svg()
        assert "<path" in svg  # bass clef path
        assert "<circle" in svg  # bass clef dots


# ═══════════════════════════════════════════════════════════════════
# Grand Staff Renderer
# ═══════════════════════════════════════════════════════════════════


class TestGrandStaffRenderer:
    def test_treble_note_position(self):
        """B4 on treble part of grand staff should be on line 3."""
        y = midi_to_grand_staff_y(71, "treble")
        expected = GRAND_TREBLE_TOP + 2 * LINE_SPACING
        assert y == expected

    def test_bass_note_position(self):
        """D3 on bass part of grand staff should be on line 3."""
        y = midi_to_grand_staff_y(50, "bass")
        expected = GRAND_BASS_TOP + 2 * LINE_SPACING
        assert y == expected

    def test_treble_and_bass_separate(self):
        """Same diatonic step should give different y for treble vs bass."""
        y_treble = midi_to_grand_staff_y(60, "treble")  # C4 on treble
        y_bass = midi_to_grand_staff_y(60, "bass")  # C4 on bass
        assert y_treble != y_bass
        # C4 on treble = ledger below staff (high y), C4 on bass = ledger above staff (low y)
        assert y_treble < y_bass

    def test_accidental_returns_none(self):
        assert midi_to_grand_staff_y(61, "treble") is None
        assert midi_to_grand_staff_y(61, "bass") is None

    def test_ledger_lines_grand_treble(self):
        """Middle C on treble staff needs a ledger line."""
        ledgers = needs_ledger_lines_grand(60, "treble")
        assert len(ledgers) >= 1

    def test_ledger_lines_grand_bass(self):
        """Middle C on bass staff needs a ledger line."""
        ledgers = needs_ledger_lines_grand(60, "bass")
        assert len(ledgers) >= 1

    def test_render_empty_grand_staff(self):
        svg = render_grand_staff_svg()
        assert "grand-staff" in svg
        assert GRAND_STAFF_HEIGHT > 0
        assert str(GRAND_STAFF_HEIGHT) in svg

    def test_render_grand_staff_with_treble_note(self):
        svg = render_grand_staff_svg(target_midi=71, target_clef="treble")
        assert "grand-staff-note" in svg
        assert "ellipse" in svg

    def test_render_grand_staff_with_bass_note(self):
        svg = render_grand_staff_svg(target_midi=50, target_clef="bass")
        assert "grand-staff-note" in svg

    def test_grand_staff_has_both_clefs(self):
        svg = render_grand_staff_svg()
        # Should have treble clef path and bass clef path/circles
        assert svg.count("<circle") >= 2  # bass clef dots

    def test_grand_staff_has_brace(self):
        svg = render_grand_staff_svg()
        assert 'stroke-width="3"' in svg  # brace line

    def test_grand_staff_has_c4_label(self):
        svg = render_grand_staff_svg()
        assert "C4" in svg


# ═══════════════════════════════════════════════════════════════════
# Exercise State
# ═══════════════════════════════════════════════════════════════════


class TestExerciseState:
    def test_generate_sequence(self):
        state = ExerciseState(note_pool=[60, 62, 64], num_notes=10)
        state.generate_sequence()
        assert len(state.sequence) == 10
        assert all(m in [60, 62, 64] for m in state.sequence)

    def test_pick_next(self):
        state = ExerciseState(note_pool=[60, 62], num_notes=3)
        state.generate_sequence()
        n1 = state.pick_next()
        assert n1 is not None
        assert n1 == state.target_midi

    def test_pick_next_returns_none_when_done(self):
        state = ExerciseState(note_pool=[60], num_notes=1)
        state.generate_sequence()
        state.pick_next()
        state.current_index = 1
        assert state.pick_next() is None

    def test_score_calculation(self):
        state = ExerciseState()
        state.hits = 8
        state.misses = 2
        assert state.score == 0.8

    def test_score_zero_when_no_attempts(self):
        state = ExerciseState()
        assert state.score == 0.0

    def test_flash_js_defines_functions(self):
        assert "flashPianoKey" in FLASH_JS
        assert "highlightPianoKeyPersist" in FLASH_JS
        assert "resetPianoKey" in FLASH_JS

    def test_flash_js_defines_active_zone(self):
        assert "setActiveZone" in FLASH_JS
        assert "clearActiveZone" in FLASH_JS
