"""Flash Cards page — quick-fire note identification drills."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from nicegui import ui

from app.keyboard.renderer import create_keyboard, is_black_key
from app.midi.bridge import MidiBridge
from app.staff.renderer import (
    midi_to_note_name,
    render_bass_staff_svg,
    render_grand_staff_svg,
    render_staff_svg,
)

# ── Constants ────────────────────────────────────────────────────

MODE_STAFF_TO_PIANO = "staff_to_piano"
MODE_NAME_TO_PIANO = "name_to_piano"
MODE_PIANO_TO_NAME = "piano_to_name"

MODE_LABELS = {
    MODE_STAFF_TO_PIANO: "Staff → Piano",
    MODE_NAME_TO_PIANO: "Name → Piano",
    MODE_PIANO_TO_NAME: "Piano → Name",
}

CLEF_RANGES = {
    "treble": (59, 81),
    "bass": (40, 60),
    "grand": (40, 81),
}

TIMER_OPTIONS = {0: "Off", 5: "5 s", 10: "10 s", 15: "15 s"}
CARD_COUNT_OPTIONS = {0: "Unlimited", 10: "10", 20: "20", 50: "50"}

DEFAULT_CLEF = "treble"
DEFAULT_MODE = MODE_STAFF_TO_PIANO
DEFAULT_TIMER = 0
DEFAULT_CARD_COUNT = 10

# ── Keyboard flash JS ───────────────────────────────────────────

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


def _build_note_pool(clef: str, include_sharps: bool) -> tuple[int, ...]:
    """Build a note pool based on clef range."""
    lo, hi = CLEF_RANGES.get(clef, CLEF_RANGES["treble"])
    pool = []
    for m in range(lo, hi + 1):
        if not include_sharps and is_black_key(m):
            continue
        pool.append(m)
    return tuple(pool)


def _normalize_note_name(name: str) -> str:
    """Normalize a user-typed note name for comparison.

    Accepts e.g. 'c4', 'C4', 'c#4', 'C#4', 'Db4' etc.
    Converts flats to sharps for matching.
    """
    s = name.strip()
    if not s:
        return ""
    # Capitalize first letter
    result = s[0].upper() + s[1:]
    # Convert common flat notation to sharp
    _FLAT_TO_SHARP = {
        "Db": "C#",
        "Eb": "D#",
        "Fb": "E",
        "Gb": "F#",
        "Ab": "G#",
        "Bb": "A#",
        "Cb": "B",
    }
    for flat, sharp in _FLAT_TO_SHARP.items():
        if result.startswith(flat):
            result = sharp + result[len(flat) :]
            break
    return result


# ── Session state ────────────────────────────────────────────────


@dataclass
class FlashCardSession:
    """Tracks state for a flash card drill session."""

    mode: str = DEFAULT_MODE
    clef: str = DEFAULT_CLEF
    note_pool: list[int] = field(default_factory=list)
    card_limit: int = DEFAULT_CARD_COUNT
    timer_seconds: int = DEFAULT_TIMER

    target_midi: int = 0
    card_index: int = 0
    hits: int = 0
    misses: int = 0
    recent_targets: list[int] = field(default_factory=list)
    response_times: list[float] = field(default_factory=list)
    card_start_time: float = 0.0
    finished: bool = False

    def pick_next(self) -> int:
        """Pick a new random target, avoiding recent repeats."""
        avoid = (
            set(self.recent_targets[-3:])
            if len(self.recent_targets) >= 3
            else set(self.recent_targets)
        )
        candidates = [n for n in self.note_pool if n not in avoid]
        if not candidates:
            candidates = list(self.note_pool)
        self.target_midi = random.choice(candidates)
        self.recent_targets.append(self.target_midi)
        if len(self.recent_targets) > 10:
            self.recent_targets = self.recent_targets[-10:]
        self.card_index += 1
        self.card_start_time = time.time()
        return self.target_midi

    def record_hit(self) -> None:
        elapsed = (
            time.time() - self.card_start_time if self.card_start_time else 0
        )
        self.hits += 1
        self.response_times.append(elapsed)

    def record_miss(self) -> None:
        elapsed = (
            time.time() - self.card_start_time if self.card_start_time else 0
        )
        self.misses += 1
        self.response_times.append(elapsed)

    def is_set_complete(self) -> bool:
        return self.card_limit > 0 and self.card_index >= self.card_limit

    def choose_clef_for_note(self, midi: int) -> str:
        if self.clef != "grand":
            return self.clef
        return "treble" if midi >= 60 else "bass"

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def accuracy(self) -> float:
        return self.hits / self.total if self.total else 0.0

    @property
    def fastest(self) -> float:
        return min(self.response_times) if self.response_times else 0.0

    @property
    def slowest(self) -> float:
        return max(self.response_times) if self.response_times else 0.0


# ── Page content ─────────────────────────────────────────────────


def content(midi: MidiBridge) -> None:
    ui.markdown(
        "Quick-fire note identification drills. "
        "Choose a mode, set your options, and start!"
    )

    # ── State ────────────────────────────────────────────────────
    session = FlashCardSession()
    active = {"value": False}
    countdown = {"value": 0}

    # UI element refs
    staff_html_ref: dict[str, ui.html | None] = {"el": None}
    prompt_label_ref: dict[str, ui.label | None] = {"el": None}
    card_counter_ref: dict[str, ui.label | None] = {"el": None}
    score_label_ref: dict[str, ui.label | None] = {"el": None}
    accuracy_label_ref: dict[str, ui.label | None] = {"el": None}
    timer_label_ref: dict[str, ui.label | None] = {"el": None}
    feedback_label_ref: dict[str, ui.label | None] = {"el": None}
    start_btn_ref: dict[str, ui.button | None] = {"el": None}
    stop_btn_ref: dict[str, ui.button | None] = {"el": None}
    answer_input_ref: dict[str, ui.input | None] = {"el": None}
    summary_card_ref: dict[str, ui.card | None] = {"el": None}
    summary_html_ref: dict[str, ui.html | None] = {"el": None}
    staff_container_ref: dict[str, ui.column | None] = {"el": None}
    input_container_ref: dict[str, ui.row | None] = {"el": None}
    timer_ref: dict[str, ui.timer | None] = {"el": None}

    config = {
        "mode": DEFAULT_MODE,
        "clef": DEFAULT_CLEF,
        "timer": DEFAULT_TIMER,
        "card_count": DEFAULT_CARD_COUNT,
        "sharps_flats": False,
    }

    # ── Helpers ──────────────────────────────────────────────────

    def _render_empty_staff() -> str:
        if config["clef"] == "bass":
            return render_bass_staff_svg()
        elif config["clef"] == "grand":
            return render_grand_staff_svg()
        return render_staff_svg()

    def _render_note(midi_val: int, clef: str) -> str:
        if config["clef"] == "bass":
            return render_bass_staff_svg(target_midi=midi_val)
        elif config["clef"] == "grand":
            return render_grand_staff_svg(
                target_midi=midi_val, target_clef=clef
            )
        return render_staff_svg(target_midi=midi_val)

    def _update_display() -> None:
        if score_label_ref["el"]:
            score_label_ref["el"].text = (
                f"Correct: {session.hits} | Wrong: {session.misses}"
            )
        if accuracy_label_ref["el"]:
            pct = int(session.accuracy * 100)
            accuracy_label_ref["el"].text = f"Accuracy: {pct}%"
        if card_counter_ref["el"]:
            if session.card_limit > 0:
                card_counter_ref["el"].text = (
                    f"Card {session.card_index}/{session.card_limit}"
                )
            else:
                card_counter_ref["el"].text = f"Card {session.card_index}"

    def _start_countdown() -> None:
        if session.timer_seconds <= 0:
            if timer_label_ref["el"]:
                timer_label_ref["el"].text = ""
            return
        countdown["value"] = session.timer_seconds
        if timer_label_ref["el"]:
            timer_label_ref["el"].text = f"⏱ {countdown['value']}s"

    def _tick() -> None:
        if not active["value"] or session.timer_seconds <= 0:
            return
        countdown["value"] -= 1
        if timer_label_ref["el"]:
            if countdown["value"] > 0:
                timer_label_ref["el"].text = f"⏱ {countdown['value']}s"
            else:
                timer_label_ref["el"].text = "⏱ Time!"
        if countdown["value"] <= 0:
            _handle_timeout()

    def _handle_timeout() -> None:
        """Auto-mark as miss when timer expires."""
        if not active["value"]:
            return
        session.record_miss()
        target_name = midi_to_note_name(session.target_midi)
        if feedback_label_ref["el"]:
            feedback_label_ref["el"].text = (
                f"⏱ Time's up! Answer: {target_name}"
            )
            feedback_label_ref["el"].classes(
                replace="text-h6 font-bold text-orange-800"
            )
        _update_display()
        _advance_card()

    def _advance_card() -> None:
        """Move to next card or finish the set."""
        if session.target_midi and session.mode != MODE_PIANO_TO_NAME:
            ui.run_javascript(f"resetPianoKey({session.target_midi})")
        if session.mode == MODE_PIANO_TO_NAME and session.target_midi:
            ui.run_javascript(f"resetPianoKey({session.target_midi})")

        if session.is_set_complete():
            _finish_set()
            return
        _show_next_card()

    def _show_next_card() -> None:
        midi_val = session.pick_next()
        note_clef = session.choose_clef_for_note(midi_val)
        _start_countdown()

        if session.mode == MODE_STAFF_TO_PIANO:
            # Show note on staff
            if staff_html_ref["el"]:
                staff_html_ref["el"].content = _render_note(
                    midi_val, note_clef
                )
            if prompt_label_ref["el"]:
                prompt_label_ref["el"].text = "Play this note!"

        elif session.mode == MODE_NAME_TO_PIANO:
            # Show note name as text
            name = midi_to_note_name(midi_val)
            if staff_html_ref["el"]:
                staff_html_ref["el"].content = _render_empty_staff()
            if prompt_label_ref["el"]:
                prompt_label_ref["el"].text = f"Play: {name}"

        elif session.mode == MODE_PIANO_TO_NAME:
            # Highlight key on keyboard, user types name
            if staff_html_ref["el"]:
                staff_html_ref["el"].content = _render_empty_staff()
            if prompt_label_ref["el"]:
                prompt_label_ref["el"].text = "Name the highlighted key!"
            ui.run_javascript(
                f"highlightPianoKeyPersist({midi_val}, '#42A5F5')"
            )
            if answer_input_ref["el"]:
                answer_input_ref["el"].value = ""

        _update_display()

    def _on_note(note: int, velocity: int) -> None:
        """Handle MIDI note-on for Staff→Piano and Name→Piano modes."""
        if not active["value"] or session.finished:
            return
        if session.mode == MODE_PIANO_TO_NAME:
            return  # Ignore MIDI in type-answer mode

        target = session.target_midi
        if note == target:
            session.record_hit()
            ui.run_javascript(f"resetPianoKey({target})")
            ui.run_javascript(f"flashPianoKey({note}, '#4CAF50', 400)")
            if feedback_label_ref["el"]:
                feedback_label_ref["el"].text = "✓ Correct!"
                feedback_label_ref["el"].classes(
                    replace="text-h6 font-bold text-green-600"
                )
        else:
            session.record_miss()
            ui.run_javascript(f"flashPianoKey({note}, '#F44336', 600)")
            target_name = midi_to_note_name(target)
            if feedback_label_ref["el"]:
                feedback_label_ref["el"].text = f"✗ Wrong — was {target_name}"
                feedback_label_ref["el"].classes(
                    replace="text-h6 font-bold text-red-600"
                )

        _update_display()
        _advance_card()

    def _on_submit_answer() -> None:
        """Handle typed answer for Piano→Name mode."""
        if not active["value"] or session.finished:
            return
        if session.mode != MODE_PIANO_TO_NAME:
            return

        answer = answer_input_ref["el"].value if answer_input_ref["el"] else ""
        expected = midi_to_note_name(session.target_midi)
        normalized_answer = _normalize_note_name(answer)
        normalized_expected = _normalize_note_name(expected)

        if normalized_answer == normalized_expected:
            session.record_hit()
            ui.run_javascript(
                f"flashPianoKey({session.target_midi}, '#4CAF50', 400)"
            )
            if feedback_label_ref["el"]:
                feedback_label_ref["el"].text = f"✓ Correct! ({expected})"
                feedback_label_ref["el"].classes(
                    replace="text-h6 font-bold text-green-600"
                )
        else:
            session.record_miss()
            ui.run_javascript(
                f"flashPianoKey({session.target_midi}, '#F44336', 600)"
            )
            if feedback_label_ref["el"]:
                feedback_label_ref["el"].text = f"✗ Wrong — was {expected}"
                feedback_label_ref["el"].classes(
                    replace="text-h6 font-bold text-red-600"
                )

        _update_display()
        _advance_card()

    def _finish_set() -> None:
        """End the session and show summary."""
        active["value"] = False
        session.finished = True
        midi.on_note_callback = None
        if timer_ref["el"]:
            timer_ref["el"].active = False

        ui.run_javascript("clearActiveZone()")
        if session.target_midi:
            ui.run_javascript(f"resetPianoKey({session.target_midi})")

        if start_btn_ref["el"]:
            start_btn_ref["el"].visible = True
        if stop_btn_ref["el"]:
            stop_btn_ref["el"].visible = False

        pct = int(session.accuracy * 100)
        fastest = f"{session.fastest:.1f}s" if session.response_times else "—"
        slowest = f"{session.slowest:.1f}s" if session.response_times else "—"

        summary = (
            f"<h3>Session Complete!</h3>"
            f"<p><b>Mode:</b> {MODE_LABELS.get(session.mode, session.mode)}</p>"
            f"<p><b>Total cards:</b> {session.total}</p>"
            f"<p><b>Correct:</b> {session.hits} &nbsp; "
            f"<b>Wrong:</b> {session.misses}</p>"
            f"<p><b>Accuracy:</b> {pct}%</p>"
            f"<p><b>Fastest:</b> {fastest} &nbsp; "
            f"<b>Slowest:</b> {slowest}</p>"
        )
        if summary_html_ref["el"]:
            summary_html_ref["el"].content = summary
        if summary_card_ref["el"]:
            summary_card_ref["el"].visible = True
        if prompt_label_ref["el"]:
            prompt_label_ref["el"].text = "Session complete!"
        if timer_label_ref["el"]:
            timer_label_ref["el"].text = ""

    def _start() -> None:
        if session.mode != MODE_PIANO_TO_NAME and not midi.connected:
            ui.notify(
                "No MIDI device connected. Select a device in the header.",
                type="warning",
                position="top",
                close_button=True,
            )
            return

        pool = _build_note_pool(config["clef"], config["sharps_flats"])
        if len(pool) < 2:
            ui.notify("Note range too narrow.", type="warning", position="top")
            return

        # Reset session
        session.mode = config["mode"]
        session.clef = config["clef"]
        session.note_pool = list(pool)
        session.card_limit = config["card_count"]
        session.timer_seconds = config["timer"]
        session.target_midi = 0
        session.card_index = 0
        session.hits = 0
        session.misses = 0
        session.recent_targets = []
        session.response_times = []
        session.finished = False
        active["value"] = True

        if start_btn_ref["el"]:
            start_btn_ref["el"].visible = False
        if stop_btn_ref["el"]:
            stop_btn_ref["el"].visible = True
        if summary_card_ref["el"]:
            summary_card_ref["el"].visible = False
        if feedback_label_ref["el"]:
            feedback_label_ref["el"].text = ""

        # Show/hide typed-answer input
        if input_container_ref["el"]:
            input_container_ref["el"].visible = (
                session.mode == MODE_PIANO_TO_NAME
            )

        midi.on_note_callback = _on_note
        lo, hi = CLEF_RANGES.get(config["clef"], CLEF_RANGES["treble"])
        ui.run_javascript(f"setActiveZone({lo}, {hi})")

        # Start timer
        if session.timer_seconds > 0 and timer_ref["el"]:
            timer_ref["el"].active = True

        _update_display()
        _show_next_card()

    def _stop() -> None:
        active["value"] = False
        midi.on_note_callback = None
        if timer_ref["el"]:
            timer_ref["el"].active = False
        if session.target_midi:
            ui.run_javascript(f"resetPianoKey({session.target_midi})")
        ui.run_javascript("clearActiveZone()")

        if start_btn_ref["el"]:
            start_btn_ref["el"].visible = True
        if stop_btn_ref["el"]:
            stop_btn_ref["el"].visible = False
        if timer_label_ref["el"]:
            timer_label_ref["el"].text = ""
        if staff_html_ref["el"]:
            staff_html_ref["el"].content = _render_empty_staff()
        if prompt_label_ref["el"]:
            prompt_label_ref["el"].text = "—"

        # Show summary if cards were played
        if session.total > 0:
            _finish_set()

    # ── UI Layout ────────────────────────────────────────────────

    with ui.row().classes("w-full gap-6"):
        # ── Config sidebar ───────────────────────────────────────
        with ui.card().classes("w-64 p-4 shrink-0"):
            ui.label("Configuration").classes("text-h6 text-blue-900 q-mb-sm")

            ui.label("Mode").classes("text-subtitle2 q-mt-sm")
            ui.select(
                options=MODE_LABELS,
                value=DEFAULT_MODE,
                on_change=lambda e: config.__setitem__("mode", e.value),
            ).props("dense outlined").classes("w-full")

            ui.label("Clef").classes("text-subtitle2 q-mt-md")
            ui.select(
                options={
                    "treble": "Treble",
                    "bass": "Bass",
                    "grand": "Both (Grand)",
                },
                value=DEFAULT_CLEF,
                on_change=lambda e: config.__setitem__("clef", e.value),
            ).props("dense outlined").classes("w-full")

            ui.separator().classes("q-my-sm")

            ui.label("Timer per card").classes("text-subtitle2")
            ui.select(
                options=TIMER_OPTIONS,
                value=DEFAULT_TIMER,
                on_change=lambda e: config.__setitem__("timer", e.value),
            ).props("dense outlined").classes("w-full")

            ui.label("Card count").classes("text-subtitle2 q-mt-md")
            ui.select(
                options=CARD_COUNT_OPTIONS,
                value=DEFAULT_CARD_COUNT,
                on_change=lambda e: config.__setitem__("card_count", e.value),
            ).props("dense outlined").classes("w-full")

            ui.separator().classes("q-my-sm")

            ui.label("Options").classes("text-subtitle2")
            ui.checkbox(
                "Include sharps/flats",
                value=False,
                on_change=lambda e: config.__setitem__(
                    "sharps_flats", e.value
                ),
            )

        # ── Main area ────────────────────────────────────────────
        with ui.column().classes("flex-grow gap-4"):
            with ui.card().classes("w-full p-4"):
                ui.label("Flash Cards").classes("text-h6")

                with ui.row().classes("items-center gap-4 q-my-sm"):
                    start_btn_ref["el"] = ui.button(
                        "Start", icon="play_arrow", on_click=_start
                    ).props("color=primary")
                    stop_btn_ref["el"] = ui.button(
                        "Stop", icon="stop", on_click=_stop
                    ).props("color=negative outline")
                    stop_btn_ref["el"].visible = False

                # Scoring row
                with ui.row().classes("items-center gap-6 q-my-sm"):
                    card_counter_ref["el"] = ui.label("Card 0").classes(
                        "text-subtitle1 text-blue-800"
                    )
                    score_label_ref["el"] = ui.label(
                        "Correct: 0 | Wrong: 0"
                    ).classes("text-subtitle1")
                    accuracy_label_ref["el"] = ui.label(
                        "Accuracy: 0%"
                    ).classes("text-subtitle1")
                    timer_label_ref["el"] = ui.label("").classes(
                        "text-subtitle1 text-orange-800 font-bold"
                    )

                # Prompt / feedback row
                prompt_label_ref["el"] = ui.label("—").classes(
                    "text-h4 font-bold text-blue-800 q-my-sm"
                )
                feedback_label_ref["el"] = ui.label("").classes(
                    "text-h6 font-bold"
                )

                # Staff display (used in staff_to_piano mode; shown empty otherwise)
                staff_container_ref["el"] = ui.column().classes("w-full")
                with staff_container_ref["el"]:
                    staff_html_ref["el"] = ui.html(
                        _render_empty_staff()
                    ).classes("w-full q-my-md")

                # Typed answer input (Piano→Name mode only)
                input_container_ref["el"] = ui.row().classes(
                    "items-center gap-4"
                )
                input_container_ref["el"].visible = False
                with input_container_ref["el"]:
                    answer_input_ref["el"] = (
                        ui.input(
                            label="Your answer (e.g. C4, F#3)",
                            on_change=None,
                        )
                        .props("dense outlined")
                        .classes("w-48")
                        .on("keydown.enter", _on_submit_answer)
                    )
                    ui.button(
                        "Submit", icon="check", on_click=_on_submit_answer
                    ).props("color=primary dense")

            # Summary card (hidden until set complete)
            summary_card_ref["el"] = ui.card().classes("w-full p-4 bg-blue-50")
            summary_card_ref["el"].visible = False
            with summary_card_ref["el"]:
                summary_html_ref["el"] = ui.html("").classes("w-full")

    # Timer (1-second tick, starts inactive)
    timer_ref["el"] = ui.timer(1.0, _tick, active=False)

    ui.run_javascript(FLASH_JS)

    # Keyboard
    ui.separator()
    ui.label("Your Keyboard").classes("text-h6")
    create_keyboard()
