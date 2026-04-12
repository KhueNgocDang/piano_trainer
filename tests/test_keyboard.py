"""Tests for keyboard profiles, SVG renderer, and highlight JS integration."""

import re

import pytest

from app.keyboard.profiles import CASIO_PRIVIA, KeyboardProfile
from app.keyboard.renderer import (
    BLACK_KEY_HEIGHT,
    BLACK_KEY_WIDTH,
    MIDDLE_C_MIDI,
    WHITE_KEY_HEIGHT,
    WHITE_KEY_STRIDE,
    WHITE_KEY_WIDTH,
    _build_white_key_map,
    is_black_key,
    midi_note_name,
    render_keyboard_svg,
)


# ── KeyboardProfile ─────────────────────────────────────────────


class TestKeyboardProfile:
    def test_casio_privia_defaults(self):
        assert CASIO_PRIVIA.name == "CASIO Privia"
        assert CASIO_PRIVIA.midi_start == 21
        assert CASIO_PRIVIA.midi_end == 108

    def test_num_keys(self):
        assert CASIO_PRIVIA.num_keys == 88

    def test_frozen(self):
        with pytest.raises(AttributeError):
            CASIO_PRIVIA.name = "Other"  # type: ignore[misc]

    def test_custom_profile(self):
        p = KeyboardProfile(name="Mini", midi_start=48, midi_end=72)
        assert p.num_keys == 25


# ── Note helpers ─────────────────────────────────────────────────


class TestNoteHelpers:
    @pytest.mark.parametrize(
        "midi,expected",
        [
            (21, False),  # A0  — white
            (22, True),  # A#0 — black
            (23, False),  # B0  — white
            (24, False),  # C1  — white
            (25, True),  # C#1 — black
            (60, False),  # C4  — white (Middle C)
            (61, True),  # C#4 — black
            (64, False),  # E4  — white
            (66, True),  # F#4 — black
            (108, False),  # C8  — white
        ],
    )
    def test_is_black_key(self, midi, expected):
        assert is_black_key(midi) is expected

    def test_black_key_count_88(self):
        blacks = sum(1 for m in range(21, 109) if is_black_key(m))
        assert blacks == 36

    def test_white_key_count_88(self):
        whites = sum(1 for m in range(21, 109) if not is_black_key(m))
        assert whites == 52

    @pytest.mark.parametrize(
        "midi,name",
        [(21, "A0"), (60, "C4"), (69, "A4"), (108, "C8"), (61, "C#4")],
    )
    def test_midi_note_name(self, midi, name):
        assert midi_note_name(midi) == name


# ── White key map ────────────────────────────────────────────────


class TestWhiteKeyMap:
    def test_length(self):
        wk = _build_white_key_map(CASIO_PRIVIA)
        assert len(wk) == 52

    def test_first_key_is_a0(self):
        wk = _build_white_key_map(CASIO_PRIVIA)
        assert wk[21] == 0  # A0 is the first white key

    def test_last_key_is_c8(self):
        wk = _build_white_key_map(CASIO_PRIVIA)
        assert wk[108] == 51  # C8 is the 52nd white key

    def test_middle_c_index(self):
        wk = _build_white_key_map(CASIO_PRIVIA)
        assert 60 in wk  # Middle C is a white key

    def test_no_black_keys_in_map(self):
        wk = _build_white_key_map(CASIO_PRIVIA)
        for midi in wk:
            assert not is_black_key(midi)


# ── SVG rendering ────────────────────────────────────────────────


class TestRenderSVG:
    @pytest.fixture
    def svg(self):
        return render_keyboard_svg(CASIO_PRIVIA)

    def test_is_valid_svg(self, svg):
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_has_viewbox(self, svg):
        assert 'viewBox="' in svg

    def test_responsive_width(self, svg):
        assert "width:100%" in svg

    def test_contains_all_88_keys(self, svg):
        for midi in range(21, 109):
            assert f'id="piano-key-{midi}"' in svg

    def test_white_key_count(self, svg):
        assert svg.count('class="piano-white-key"') == 52

    def test_black_key_count(self, svg):
        assert svg.count('class="piano-black-key"') == 36

    def test_white_key_dimensions(self, svg):
        assert f'width="{WHITE_KEY_WIDTH}"' in svg
        assert f'height="{WHITE_KEY_HEIGHT}"' in svg

    def test_black_key_dimensions(self, svg):
        assert f'width="{BLACK_KEY_WIDTH}"' in svg
        assert f'height="{BLACK_KEY_HEIGHT}"' in svg

    def test_middle_c_marker(self, svg):
        # Gold circle + "C4" label
        assert MIDDLE_C_MIDI == 60
        assert "<circle" in svg
        assert ">C4</text>" in svg

    def test_data_attributes_on_white_key(self, svg):
        # Check that a white key (e.g. C4) has data attributes
        match = re.search(r'id="piano-key-60"[^/]*', svg)
        assert match
        key_str = match.group()
        assert "data-default-color" in key_str
        assert "data-active-color" in key_str

    def test_data_attributes_on_black_key(self, svg):
        # Check that a black key (e.g. C#4 = MIDI 61) has data attributes
        match = re.search(r'id="piano-key-61"[^/]*', svg)
        assert match
        key_str = match.group()
        assert "data-default-color" in key_str
        assert "data-active-color" in key_str

    def test_octave_labels_present(self, svg):
        # C1 through C8
        for octave in range(1, 9):
            assert f">C{octave}</text>" in svg

    def test_a0_label(self, svg):
        assert ">A0</text>" in svg

    def test_white_keys_in_order(self, svg):
        """First white key has x=0, second has x=STRIDE."""
        assert 'id="piano-key-21"' in svg  # A0
        assert f'x="0" y="0" width="{WHITE_KEY_WIDTH}"' in svg
        assert f'x="{WHITE_KEY_STRIDE}" y="0" width="{WHITE_KEY_WIDTH}"' in svg


# ── Highlight JS ─────────────────────────────────────────────────


class TestHighlightJS:
    def test_highlight_function_in_midi_js(self):
        from app.midi.midi_js import MIDI_JS

        assert "highlightKey" in MIDI_JS
        assert "unhighlightKey" in MIDI_JS

    def test_highlight_uses_data_attributes(self):
        from app.midi.midi_js import MIDI_JS

        assert "dataset.activeColor" in MIDI_JS
        assert "dataset.defaultColor" in MIDI_JS

    def test_highlight_targets_piano_key_id(self):
        from app.midi.midi_js import MIDI_JS

        assert "piano-key-" in MIDI_JS
