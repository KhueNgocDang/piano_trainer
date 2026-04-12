"""Note drill — generates random notes on the treble clef staff and checks MIDI input."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from nicegui import ui

from app.keyboard.renderer import is_black_key
from app.staff.renderer import (
    midi_to_note_name,
    render_staff_svg,
)

# Treble clef natural notes: C4 (60) to C6 (84), excluding sharps/flats
TREBLE_NATURAL_RANGE = [m for m in range(60, 85) if not is_black_key(m)]


@dataclass
class DrillState:
    """Tracks the current drill session state."""

    target_midi: int = 0
    hits: int = 0
    misses: int = 0
    total: int = 0
    recent_targets: list[int] = field(default_factory=list)

    def pick_next(self) -> int:
        """Pick a new random target, avoiding recent repeats."""
        avoid = (
            set(self.recent_targets[-3:])
            if len(self.recent_targets) >= 3
            else set(self.recent_targets)
        )
        candidates = [n for n in TREBLE_NATURAL_RANGE if n not in avoid]
        if not candidates:
            candidates = TREBLE_NATURAL_RANGE
        self.target_midi = random.choice(candidates)
        self.recent_targets.append(self.target_midi)
        if len(self.recent_targets) > 10:
            self.recent_targets = self.recent_targets[-10:]
        return self.target_midi


# ── Keyboard feedback JS (flash green/red/blue) ─────────────────

FLASH_JS = """
(function() {
    window._pianoFlashTimers = window._pianoFlashTimers || {};

    window.flashPianoKey = function(midi, color, durationMs) {
        const el = document.getElementById('piano-key-' + midi);
        if (!el) return;
        const orig = el.dataset.defaultColor;
        el.setAttribute('fill', color);
        if (window._pianoFlashTimers[midi]) clearTimeout(window._pianoFlashTimers[midi]);
        window._pianoFlashTimers[midi] = setTimeout(() => {
            el.setAttribute('fill', orig);
            delete window._pianoFlashTimers[midi];
        }, durationMs || 600);
    };

    window.highlightPianoKeyPersist = function(midi, color) {
        const el = document.getElementById('piano-key-' + midi);
        if (!el) return;
        el.setAttribute('fill', color);
    };

    window.resetPianoKey = function(midi) {
        const el = document.getElementById('piano-key-' + midi);
        if (!el) return;
        el.setAttribute('fill', el.dataset.defaultColor);
    };
})();
"""


class NoteDrill:
    """NiceGUI component that manages a treble clef note-reading drill."""

    def __init__(self, midi_bridge) -> None:
        self._bridge = midi_bridge
        self._state = DrillState()
        self._staff_html: ui.html | None = None
        self._score_label: ui.label | None = None
        self._feedback_label: ui.label | None = None
        self._active = False

    def create_ui(self) -> None:
        """Build the drill UI elements."""
        with ui.card().classes("w-full p-4"):
            ui.label("Note Reading Drill").classes("text-h6")
            ui.markdown(
                "A note appears on the staff. Play the matching key on your piano. "
                "**Green** = correct, **Red** = wrong (blue shows the right key)."
            )

            with ui.row().classes("items-center gap-4 q-my-sm"):
                self._start_btn = ui.button(
                    "Start Drill", icon="play_arrow", on_click=self._start
                ).props("color=primary")
                self._stop_btn = ui.button(
                    "Stop", icon="stop", on_click=self._stop
                ).props("color=negative outline")
                self._stop_btn.visible = False
                self._score_label = ui.label("Hits: 0 / Misses: 0").classes(
                    "text-subtitle1"
                )

            self._feedback_label = ui.label("").classes(
                "text-subtitle2 q-my-xs"
            )

            self._staff_html = ui.html(render_staff_svg()).classes(
                "w-full q-my-md"
            )

        # Inject flash JS
        ui.run_javascript(FLASH_JS)

    def _start(self) -> None:
        """Start or restart the drill."""
        self._state = DrillState()
        self._active = True
        self._start_btn.visible = False
        self._stop_btn.visible = True
        self._update_score()
        if self._feedback_label:
            self._feedback_label.text = ""
        self._next_note()
        # Register note handler on bridge
        self._bridge.on_note_callback = self._on_note

    def _stop(self) -> None:
        """Stop the drill."""
        self._active = False
        self._start_btn.visible = True
        self._stop_btn.visible = False
        self._bridge.on_note_callback = None
        if self._feedback_label:
            total = self._state.hits + self._state.misses
            if total > 0:
                pct = self._state.hits / total * 100
                self._feedback_label.text = f"Session complete! {self._state.hits}/{total} correct ({pct:.0f}%)"

    def _next_note(self) -> None:
        """Pick and display the next target note."""
        midi = self._state.pick_next()
        if self._staff_html:
            self._staff_html.content = render_staff_svg(target_midi=midi)

    def _on_note(self, note: int, velocity: int) -> None:
        """Handle a MIDI note_on from the bridge."""
        if not self._active:
            return

        target = self._state.target_midi
        self._state.total += 1

        if note == target:
            # Correct!
            self._state.hits += 1
            ui.run_javascript(
                f"flashPianoKey({note}, '#4CAF50', 500)"
            )  # green
            if self._feedback_label:
                name = midi_to_note_name(target)
                self._feedback_label.text = f"✓ Correct! {name}"
                self._feedback_label.classes(
                    replace="text-subtitle2 q-my-xs text-green-600"
                )
            self._update_score()
            self._next_note()
        else:
            # Wrong
            self._state.misses += 1
            ui.run_javascript(
                f"flashPianoKey({note}, '#F44336', 500)"
            )  # red flash played key
            ui.run_javascript(
                f"flashPianoKey({target}, '#2196F3', 1200)"
            )  # blue hint target
            if self._feedback_label:
                played_name = midi_to_note_name(note)
                target_name = midi_to_note_name(target)
                self._feedback_label.text = (
                    f"✗ You played {played_name}, expected {target_name}"
                )
                self._feedback_label.classes(
                    replace="text-subtitle2 q-my-xs text-red-600"
                )
            self._update_score()

    def _update_score(self) -> None:
        if self._score_label:
            self._score_label.text = (
                f"Hits: {self._state.hits} / Misses: {self._state.misses}"
            )
