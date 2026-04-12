"""Keyboard profile definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KeyboardProfile:
    """Describes a physical keyboard's note range and layout."""

    name: str
    midi_start: int  # lowest MIDI note number
    midi_end: int  # highest MIDI note number

    @property
    def num_keys(self) -> int:
        return self.midi_end - self.midi_start + 1


# CASIO Privia PX-S series — 88 keys, A0 (MIDI 21) to C8 (MIDI 108)
CASIO_PRIVIA = KeyboardProfile(
    name="CASIO Privia", midi_start=21, midi_end=108
)
