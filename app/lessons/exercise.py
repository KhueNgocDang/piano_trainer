"""Lesson exercise engine — similar to NoteDrill but driven by lesson data."""

from __future__ import annotations

import inspect
import random
from dataclasses import dataclass, field

from nicegui import background_tasks, ui

from app.keyboard.renderer import is_black_key
from app.lessons.models import Clef, Exercise
from app.staff.renderer import (
    midi_to_note_name,
    render_bass_staff_svg,
    render_grand_staff_svg,
    render_staff_svg,
)

# Keyboard feedback JS (same as drill.py — reuse via injection)
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

    window.setActiveZone = function(minMidi, maxMidi) {
        document.querySelectorAll('[id^="piano-key-"]').forEach(el => {
            const midi = parseInt(el.id.replace('piano-key-', ''), 10);
            if (isNaN(midi)) return;
            if (midi >= minMidi && midi <= maxMidi) {
                el.style.opacity = '1.0';
            } else {
                el.style.opacity = '0.25';
            }
        });
    };

    window.clearActiveZone = function() {
        document.querySelectorAll('[id^="piano-key-"]').forEach(el => {
            el.style.opacity = '1.0';
        });
    };
})();
"""


@dataclass
class ExerciseState:
    """Tracks state for a single exercise attempt."""

    note_pool: list[int] = field(default_factory=list)
    num_notes: int = 10
    current_index: int = 0
    target_midi: int = 0
    target_clef: str = "treble"
    hits: int = 0
    misses: int = 0
    sequence: list[int] = field(default_factory=list)
    recent_targets: list[int] = field(default_factory=list)

    def generate_sequence(self) -> None:
        """Pre-generate a shuffled sequence of notes to present."""
        pool = list(self.note_pool)
        self.sequence = []
        while len(self.sequence) < self.num_notes:
            random.shuffle(pool)
            self.sequence.extend(pool)
        self.sequence = self.sequence[: self.num_notes]

    def pick_next(self) -> int | None:
        """Pick the next note from the sequence. Returns None when done."""
        if self.current_index >= self.num_notes:
            return None
        midi = self.sequence[self.current_index]
        self.target_midi = midi
        return midi

    @property
    def score(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class LessonExercise:
    """NiceGUI component for an interactive lesson exercise."""

    def __init__(
        self, exercise: Exercise, midi_bridge, on_complete=None
    ) -> None:
        self._exercise = exercise
        self._bridge = midi_bridge
        self._on_complete = on_complete  # callback(score: float, passed: bool)
        self._state = ExerciseState(
            note_pool=list(exercise.note_pool),
            num_notes=exercise.num_notes,
        )
        self._staff_html: ui.html | None = None
        self._score_label: ui.label | None = None
        self._feedback_label: ui.label | None = None
        self._progress_label: ui.label | None = None
        self._target_label: ui.label | None = None
        self._played_label: ui.label | None = None
        self._start_btn: ui.button | None = None
        self._active = False

    def create_ui(self) -> None:
        """Build the exercise UI."""
        with ui.card().classes("w-full p-4 bg-blue-50"):
            ui.label("Exercise").classes("text-h6 text-blue-900")
            threshold_pct = int(self._exercise.pass_threshold * 100)
            ui.label(
                f"Play {self._exercise.num_notes} notes correctly. "
                f"You need ≥{threshold_pct}% accuracy to pass."
            ).classes("text-body2 text-grey-8")

            with ui.row().classes("items-center gap-4 q-my-sm"):
                self._start_btn = ui.button(
                    "Start Exercise", icon="play_arrow", on_click=self._start
                ).props("color=primary")
                self._progress_label = ui.label("").classes("text-subtitle1")
                self._score_label = ui.label("").classes("text-subtitle1")

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

            # Staff display
            self._staff_html = ui.html(self._render_empty_staff()).classes(
                "w-full q-my-md"
            )

        ui.run_javascript(FLASH_JS)

    def _render_empty_staff(self) -> str:
        if self._exercise.clef == Clef.BASS:
            return render_bass_staff_svg()
        elif self._exercise.clef == Clef.GRAND:
            return render_grand_staff_svg()
        else:
            return render_staff_svg()

    def _render_note(self, midi: int) -> str:
        if self._exercise.clef == Clef.BASS:
            return render_bass_staff_svg(target_midi=midi)
        elif self._exercise.clef == Clef.GRAND:
            clef = self._choose_clef_for_note(midi)
            self._state.target_clef = clef
            return render_grand_staff_svg(target_midi=midi, target_clef=clef)
        else:
            return render_staff_svg(target_midi=midi)

    def _choose_clef_for_note(self, midi: int) -> str:
        """Choose which clef to display a note on for grand staff exercises."""
        if midi >= 60:
            return "treble"
        return "bass"

    def _start(self) -> None:
        if not self._bridge.connected:
            ui.notify(
                "No MIDI device connected. Please select a device in the header first.",
                type="warning",
                position="top",
                close_button=True,
            )
            return

        self._state = ExerciseState(
            note_pool=list(self._exercise.note_pool),
            num_notes=self._exercise.num_notes,
        )
        self._state.generate_sequence()
        self._active = True
        if self._start_btn:
            self._start_btn.visible = False
        self._update_display()
        self._next_note()
        self._bridge.on_note_callback = self._on_note

        # Dim keys outside the exercise note pool range
        pool = self._exercise.note_pool
        if pool:
            ui.run_javascript(f"setActiveZone({min(pool)}, {max(pool)})")

    def _next_note(self) -> None:
        """Show the next note or finish."""
        if self._state.target_midi:
            ui.run_javascript(f"resetPianoKey({self._state.target_midi})")

        midi = self._state.pick_next()
        if midi is None:
            self._finish()
            return

        if self._staff_html:
            self._staff_html.content = self._render_note(midi)
        if self._target_label:
            self._target_label.text = midi_to_note_name(midi)
        ui.run_javascript(f"highlightPianoKeyPersist({midi}, '#42A5F5')")
        self._update_display()

    def _on_note(self, note: int, velocity: int) -> None:
        if not self._active:
            return

        target = self._state.target_midi
        played_name = midi_to_note_name(note)
        if self._played_label:
            self._played_label.text = played_name

        if note == target:
            self._state.hits += 1
            self._state.current_index += 1
            ui.run_javascript(f"resetPianoKey({target})")
            ui.run_javascript(f"flashPianoKey({note}, '#4CAF50', 400)")
            if self._played_label:
                self._played_label.classes(
                    replace="text-h5 font-bold text-green-600"
                )
            if self._feedback_label:
                self._feedback_label.text = "✓ Correct!"
                self._feedback_label.classes(
                    replace="text-h6 font-bold q-ml-md text-green-600"
                )
            self._update_display()
            self._next_note()
        else:
            self._state.misses += 1
            ui.run_javascript(f"flashPianoKey({note}, '#F44336', 600)")
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
            self._update_display()

    def _update_display(self) -> None:
        if self._progress_label:
            self._progress_label.text = (
                f"Note {min(self._state.current_index + 1, self._state.num_notes)}"
                f" / {self._state.num_notes}"
            )
        if self._score_label:
            self._score_label.text = (
                f"Hits: {self._state.hits} | Misses: {self._state.misses}"
            )

    def _finish(self) -> None:
        self._active = False
        self._bridge.on_note_callback = None
        if self._state.target_midi:
            ui.run_javascript(f"resetPianoKey({self._state.target_midi})")

        # Restore full keyboard visibility
        ui.run_javascript("clearActiveZone()")

        score = self._state.score
        passed = score >= self._exercise.pass_threshold
        pct = int(score * 100)
        threshold_pct = int(self._exercise.pass_threshold * 100)

        if self._feedback_label:
            if passed:
                self._feedback_label.text = f"🎉 Passed! {pct}% accuracy"
                self._feedback_label.classes(
                    replace="text-h6 font-bold q-ml-md text-green-600"
                )
            else:
                self._feedback_label.text = f"Score: {pct}% — need ≥{threshold_pct}% to pass. Try again!"
                self._feedback_label.classes(
                    replace="text-h6 font-bold q-ml-md text-orange-700"
                )

        if self._target_label:
            self._target_label.text = "—"
        if self._start_btn:
            self._start_btn.text = (
                "Retry Exercise" if not passed else "Play Again"
            )
            self._start_btn.visible = True

        if self._on_complete:
            result = self._on_complete(score, passed)
            if inspect.isawaitable(result):
                background_tasks.create(result)
