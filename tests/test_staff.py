"""Tests for treble clef staff renderer and note drill logic."""

import pytest

from app.keyboard.renderer import is_black_key
from app.staff.renderer import (
    LINE_SPACING,
    STAFF_LINE_YS,
    STAFF_TOP,
    midi_to_note_name,
    midi_to_staff_y,
    needs_ledger_lines,
    render_staff_svg,
    _midi_to_diatonic_steps_from_b4,
)
from app.staff.drill import (
    TREBLE_NATURAL_RANGE,
    DrillState,
    FLASH_JS,
)


# ── midi_to_staff_y ─────────────────────────────────────────────


class TestMidiToStaffY:
    def test_b4_on_line3(self):
        """B4 (MIDI 71) sits on line 3 (top index 2)."""
        y = midi_to_staff_y(71)
        assert y == STAFF_LINE_YS[2]

    def test_e4_on_line1(self):
        """E4 (MIDI 64) sits on line 1 (bottom, top index 4)."""
        y = midi_to_staff_y(64)
        assert y == STAFF_LINE_YS[4]

    def test_g4_on_line2(self):
        """G4 (MIDI 67) sits on line 2 (top index 3)."""
        y = midi_to_staff_y(67)
        assert y == STAFF_LINE_YS[3]

    def test_d5_on_line4(self):
        """D5 (MIDI 74) sits on line 4 (top index 1)."""
        y = midi_to_staff_y(74)
        assert y == STAFF_LINE_YS[1]

    def test_f5_on_line5(self):
        """F5 (MIDI 77) sits on line 5 (top index 0)."""
        y = midi_to_staff_y(77)
        assert y == STAFF_LINE_YS[0]

    def test_middle_c_below_staff(self):
        """C4 (MIDI 60) is below the staff."""
        y = midi_to_staff_y(60)
        assert y is not None
        assert y > STAFF_LINE_YS[4]  # below bottom line

    def test_f4_in_space_1_2(self):
        """F4 (MIDI 65) is in the space between lines 1 and 2."""
        y = midi_to_staff_y(65)
        assert y is not None
        assert STAFF_LINE_YS[4] > y > STAFF_LINE_YS[3]  # between line 1 and 2

    def test_a4_in_space_2_3(self):
        """A4 (MIDI 69) is in the space between lines 2 and 3."""
        y = midi_to_staff_y(69)
        assert y is not None
        assert STAFF_LINE_YS[3] > y > STAFF_LINE_YS[2]

    def test_sharps_return_none(self):
        """Accidentals are not supported yet."""
        assert midi_to_staff_y(61) is None  # C#4
        assert midi_to_staff_y(66) is None  # F#4

    def test_notes_go_up(self):
        """Higher MIDI notes → lower y values (up on screen)."""
        y60 = midi_to_staff_y(60)  # C4
        y72 = midi_to_staff_y(72)  # C5
        y84 = midi_to_staff_y(84)  # C6
        assert y60 is not None and y72 is not None and y84 is not None
        assert y60 > y72 > y84

    def test_half_step_spacing(self):
        """Adjacent diatonic notes differ by LINE_SPACING / 2."""
        y_e4 = midi_to_staff_y(64)  # E4
        y_f4 = midi_to_staff_y(65)  # F4
        assert y_e4 is not None and y_f4 is not None
        assert abs((y_e4 - y_f4) - LINE_SPACING / 2) < 0.01


# ── Diatonic steps ──────────────────────────────────────────────


class TestDiatonicSteps:
    def test_b4_is_zero(self):
        assert _midi_to_diatonic_steps_from_b4(71) == 0

    def test_c5_is_one(self):
        assert _midi_to_diatonic_steps_from_b4(72) == 1

    def test_a4_is_minus_one(self):
        assert _midi_to_diatonic_steps_from_b4(69) == -1

    def test_c4_is_minus_six(self):
        """C4 is 6 diatonic steps below B4."""
        assert _midi_to_diatonic_steps_from_b4(60) == -6

    def test_c6_is_eight(self):
        """C6 is 8 diatonic steps above B4."""
        assert _midi_to_diatonic_steps_from_b4(84) == 8

    def test_accidental_returns_none(self):
        assert _midi_to_diatonic_steps_from_b4(61) is None  # C#4


# ── Ledger lines ────────────────────────────────────────────────


class TestLedgerLines:
    def test_middle_c_has_one_ledger(self):
        ledgers = needs_ledger_lines(60)
        assert len(ledgers) == 1

    def test_e4_no_ledger(self):
        """E4 is on line 1 — no ledger needed."""
        assert needs_ledger_lines(64) == []

    def test_b4_no_ledger(self):
        """B4 is on line 3 — no ledger needed."""
        assert needs_ledger_lines(71) == []

    def test_c6_has_ledger(self):
        """C6 is above the staff — needs a ledger line."""
        ledgers = needs_ledger_lines(84)
        assert len(ledgers) >= 1

    def test_accidental_empty(self):
        assert needs_ledger_lines(61) == []


# ── Note names ──────────────────────────────────────────────────


class TestMidiToNoteName:
    @pytest.mark.parametrize(
        "midi,name",
        [
            (60, "C4"),
            (71, "B4"),
            (72, "C5"),
            (84, "C6"),
            (69, "A4"),
            (61, "C#4"),
        ],
    )
    def test_note_names(self, midi, name):
        assert midi_to_note_name(midi) == name


# ── SVG rendering ───────────────────────────────────────────────


class TestRenderStaffSVG:
    def test_empty_staff(self):
        svg = render_staff_svg()
        assert "<svg" in svg
        assert 'id="treble-staff"' in svg
        assert svg.count("<line") == 5  # staff lines only

    def test_staff_with_note(self):
        svg = render_staff_svg(target_midi=60)
        assert "<ellipse" in svg
        assert 'id="staff-note"' in svg

    def test_staff_with_note_has_ledger(self):
        svg = render_staff_svg(target_midi=60)
        # Middle C: 5 staff + 1 ledger + 1 stem = 7 <line elements
        assert svg.count("<line") == 7

    def test_staff_line_note_no_extra_ledger(self):
        svg = render_staff_svg(target_midi=64)  # E4 on line 1
        assert svg.count("<line") == 6  # 5 staff lines + 1 stem

    def test_note_has_stem(self):
        svg = render_staff_svg(target_midi=60)
        # Should have lines: 5 staff + 1 ledger + 1 stem = 7
        assert svg.count("<line") >= 6

    def test_responsive(self):
        svg = render_staff_svg()
        assert "width:100%" in svg

    def test_custom_note_id(self):
        svg = render_staff_svg(target_midi=72, note_id="my-note")
        assert 'id="my-note"' in svg

    def test_hidden_label(self):
        svg = render_staff_svg(target_midi=60)
        assert 'id="staff-note-label"' in svg
        assert "display:none" in svg

    def test_treble_clef_present(self):
        svg = render_staff_svg()
        assert "<path" in svg  # clef path


# ── DrillState ──────────────────────────────────────────────────


class TestDrillState:
    def test_pick_next_in_range(self):
        state = DrillState()
        for _ in range(20):
            midi = state.pick_next()
            assert midi in TREBLE_NATURAL_RANGE

    def test_no_excessive_repeats(self):
        """After 20 picks, no more than 3 consecutive same notes."""
        state = DrillState()
        notes = [state.pick_next() for _ in range(20)]
        for i in range(len(notes) - 3):
            assert not (
                notes[i] == notes[i + 1] == notes[i + 2] == notes[i + 3]
            ), f"Four repeats in a row at index {i}: {notes[i]}"

    def test_hits_and_misses_start_zero(self):
        state = DrillState()
        assert state.hits == 0
        assert state.misses == 0

    def test_recent_targets_capped(self):
        state = DrillState()
        for _ in range(15):
            state.pick_next()
        assert len(state.recent_targets) <= 10


# ── TREBLE_NATURAL_RANGE ────────────────────────────────────────


class TestTrebleRange:
    def test_no_black_keys(self):
        for m in TREBLE_NATURAL_RANGE:
            assert not is_black_key(m), f"MIDI {m} is a black key"

    def test_starts_at_c4(self):
        assert TREBLE_NATURAL_RANGE[0] == 60

    def test_ends_at_c6(self):
        assert TREBLE_NATURAL_RANGE[-1] == 84

    def test_count(self):
        # C4 to C6 naturals: C D E F G A B × 2 octaves + final C = 15
        assert len(TREBLE_NATURAL_RANGE) == 15


# ── Flash JS ────────────────────────────────────────────────────


class TestFlashJS:
    def test_flash_function_defined(self):
        assert "flashPianoKey" in FLASH_JS

    def test_highlight_persist_defined(self):
        assert "highlightPianoKeyPersist" in FLASH_JS

    def test_reset_defined(self):
        assert "resetPianoKey" in FLASH_JS

    def test_uses_dataset(self):
        assert "dataset.defaultColor" in FLASH_JS


# ── Bridge callback ─────────────────────────────────────────────


class TestBridgeNoteCallback:
    def test_callback_fires_on_note_on(self, bridge):
        received = []
        bridge.on_note_callback = lambda note, vel: received.append(
            (note, vel)
        )
        bridge._on_note_on({"note": 60, "velocity": 80, "name": "C4"})
        assert received == [(60, 80)]

    def test_callback_not_fired_on_zero_velocity(self, bridge):
        received = []
        bridge.on_note_callback = lambda note, vel: received.append(
            (note, vel)
        )
        bridge._on_note_on({"note": 60, "velocity": 0, "name": "C4"})
        assert received == []

    def test_no_callback_when_none(self, bridge):
        bridge.on_note_callback = None
        bridge._on_note_on({"note": 60, "velocity": 80, "name": "C4"})
        # Should not raise
