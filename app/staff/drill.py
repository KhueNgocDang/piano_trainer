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
        self._played_label: ui.label | None = None
        self._target_label: ui.label | None = None
        self._active = False

    def create_ui(self) -> None:
        """Build the drill UI elements."""
        with ui.card().classes("w-full p-4"):
            ui.label("Note Reading Drill").classes("text-h6")
            ui.markdown(
                "A note appears on the staff. Play the matching key on your piano."
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

            # Feedback row: target + played note + result
            with ui.row().classes("items-center gap-6 q-my-sm"):
                with ui.column().classes("items-center gap-0"):
                    ui.label("Target").classes("text-caption text-grey-6")
                    self._target_label = ui.label("—").classes(
                        "text-h5 font-bold text-blue-800"
                    )
                with ui.column().classes("items-center gap-0"):
                    ui.label("You played").classes("text-caption text-grey-6")
                    self._played_label = ui.label("—").classes(
                        "text-h5 font-bold text-grey-5"
                    )
                self._feedback_label = ui.label("").classes(
                    "text-h6 font-bold q-ml-md"
                )

            self._staff_html = ui.html(render_staff_svg()).classes(
                "w-full q-my-md"
            )

        # Inject flash JS
        ui.run_javascript(FLASH_JS)

    def _start(self) -> None:
        """Start or restart the drill."""
        if not self._bridge.connected:
            ui.notify(
                "No MIDI device connected. Please select a device in the header first.",
                type="warning",
                position="top",
                close_button=True,
            )
            return
        self._state = DrillState()
        self._active = True
        self._start_btn.visible = False
        self._stop_btn.visible = True
        self._update_score()
        if self._feedback_label:
            self._feedback_label.text = ""
        if self._played_label:
            self._played_label.text = "—"
            self._played_label.classes(replace="text-h5 font-bold text-grey-5")
        self._next_note()
        # Register note handler on bridge
        self._bridge.on_note_callback = self._on_note

    def _stop(self) -> None:
        """Stop the drill."""
        self._active = False
        self._start_btn.visible = True
        self._stop_btn.visible = False
        self._bridge.on_note_callback = None
        # Clear target highlight
        ui.run_javascript(f"resetPianoKey({self._state.target_midi})")
        if self._target_label:
            self._target_label.text = "—"
        if self._feedback_label:
            total = self._state.hits + self._state.misses
            if total > 0:
                pct = self._state.hits / total * 100
                self._feedback_label.text = (
                    f"Done! {self._state.hits}/{total} ({pct:.0f}%)"
                )
                self._feedback_label.classes(
                    replace="text-h6 font-bold q-ml-md text-blue-800"
                )

    def _next_note(self) -> None:
        """Pick and display the next target note."""
        # Clear previous target highlight
        if self._state.target_midi:
            ui.run_javascript(f"resetPianoKey({self._state.target_midi})")

        midi = self._state.pick_next()
        if self._staff_html:
            self._staff_html.content = render_staff_svg(target_midi=midi)

        # Show target note name
        if self._target_label:
            self._target_label.text = midi_to_note_name(midi)

        # Highlight the target key on the keyboard in blue
        ui.run_javascript(f"highlightPianoKeyPersist({midi}, '#42A5F5')")

    def _on_note(self, note: int, velocity: int) -> None:
        """Handle a MIDI note_on from the bridge."""
        if not self._active:
            return

        target = self._state.target_midi
        self._state.total += 1
        played_name = midi_to_note_name(note)

        # Show what they played
        if self._played_label:
            self._played_label.text = played_name

        if note == target:
            # Correct!
            self._state.hits += 1
            ui.run_javascript(f"resetPianoKey({target})")  # clear blue hint
            ui.run_javascript(
                f"flashPianoKey({note}, '#4CAF50', 400)"
            )  # green
            if self._played_label:
                self._played_label.classes(
                    replace="text-h5 font-bold text-green-600"
                )
            if self._feedback_label:
                self._feedback_label.text = "✓ Correct!"
                self._feedback_label.classes(
                    replace="text-h6 font-bold q-ml-md text-green-600"
                )
            self._update_score()
            self._next_note()
        else:
            # Wrong
            self._state.misses += 1
            ui.run_javascript(f"flashPianoKey({note}, '#F44336', 600)")  # red
            # Keep target blue (already highlighted)
            if self._played_label:
                self._played_label.classes(
                    replace="text-h5 font-bold text-red-600"
                )
            if self._feedback_label:
                target_name = midi_to_note_name(target)
                self._feedback_label.text = f"✗ Wrong — play {target_name}"
                self._feedback_label.classes(
                    replace="text-h6 font-bold q-ml-md text-red-600"
                )
            self._update_score()

    def _update_score(self) -> None:
        if self._score_label:
            self._score_label.text = (
                f"Hits: {self._state.hits} / Misses: {self._state.misses}"
            )
