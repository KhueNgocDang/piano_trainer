"""Practice page — configurable sight-reading drill with session scoring."""

from __future__ import annotations

import inspect
import random
from dataclasses import dataclass, field

from nicegui import ui

from app.keyboard.renderer import create_keyboard, is_black_key
from app.midi.bridge import MidiBridge
from app.staff.renderer import (
    KEY_SIGNATURES,
    midi_to_note_name,
    render_bass_staff_svg,
    render_grand_staff_svg,
    render_staff_svg,
)

# ── Note range helpers ───────────────────────────────────────────

# Natural notes only (white keys) across the full keyboard range
_ALL_NATURALS = tuple(m for m in range(21, 109) if not is_black_key(m))

# Defaults
DEFAULT_CLEF = "treble"
DEFAULT_MIN_MIDI = 60  # C4
DEFAULT_MAX_MIDI = 81  # A5
DEFAULT_SHARPS_FLATS = False
DEFAULT_LEDGER_LINES = True

# Clef-appropriate ranges
CLEF_RANGES = {
    "treble": (59, 81),  # B3 – A5
    "bass": (40, 60),  # E2 – C4
    "grand": (40, 81),  # E2 – A5
}


# ── Keyboard flash JS (same as drill/exercise) ──────────────────

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


def _build_note_pool(
    clef: str, min_midi: int, max_midi: int, include_sharps: bool
) -> tuple[int, ...]:
    """Build a note pool based on configuration."""
    pool = []
    for m in range(min_midi, max_midi + 1):
        if not include_sharps and is_black_key(m):
            continue
        pool.append(m)
    return tuple(pool)


@dataclass
class PracticeSession:
    """Tracks state for a free-form practice session."""

    note_pool: list[int] = field(default_factory=list)
    clef: str = "treble"
    target_midi: int = 0
    hits: int = 0
    misses: int = 0
    streak: int = 0
    best_streak: int = 0
    recent_targets: list[int] = field(default_factory=list)

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
        return self.target_midi

    def choose_clef_for_note(self, midi: int) -> str:
        """Choose which clef to display a note on for grand staff."""
        if self.clef != "grand":
            return self.clef
        if midi >= 60:
            return "treble"
        return "bass"

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return self.hits / self.total


def content(midi: MidiBridge) -> None:
    ui.markdown(
        "Practice sight-reading with configurable difficulty. "
        "Choose your clef, note range, and start playing!"
    )

    # ── State ────────────────────────────────────────────────────
    session = PracticeSession()
    active = {"value": False}

    # UI element refs
    staff_html_ref: dict[str, ui.html | None] = {"el": None}
    score_label_ref: dict[str, ui.label | None] = {"el": None}
    accuracy_label_ref: dict[str, ui.label | None] = {"el": None}
    streak_label_ref: dict[str, ui.label | None] = {"el": None}
    best_streak_label_ref: dict[str, ui.label | None] = {"el": None}
    feedback_label_ref: dict[str, ui.label | None] = {"el": None}
    target_label_ref: dict[str, ui.label | None] = {"el": None}
    played_label_ref: dict[str, ui.label | None] = {"el": None}
    start_btn_ref: dict[str, ui.button | None] = {"el": None}
    stop_btn_ref: dict[str, ui.button | None] = {"el": None}
    new_session_btn_ref: dict[str, ui.button | None] = {"el": None}

    # Config state
    config = {
        "clef": DEFAULT_CLEF,
        "min_midi": DEFAULT_MIN_MIDI,
        "max_midi": DEFAULT_MAX_MIDI,
        "sharps_flats": DEFAULT_SHARPS_FLATS,
        "ledger_lines": DEFAULT_LEDGER_LINES,
        "key_signature": None,
    }

    # ── Helpers ──────────────────────────────────────────────────

    def _render_empty_staff() -> str:
        ks = config["key_signature"]
        if config["clef"] == "bass":
            return render_bass_staff_svg(key_signature=ks)
        elif config["clef"] == "grand":
            return render_grand_staff_svg(key_signature=ks)
        return render_staff_svg(key_signature=ks)

    def _render_note(midi: int, clef: str) -> str:
        ks = config["key_signature"]
        if config["clef"] == "bass":
            return render_bass_staff_svg(target_midi=midi, key_signature=ks)
        elif config["clef"] == "grand":
            return render_grand_staff_svg(
                target_midi=midi, target_clef=clef, key_signature=ks
            )
        return render_staff_svg(target_midi=midi, key_signature=ks)

    def _update_display() -> None:
        if score_label_ref["el"]:
            score_label_ref["el"].text = (
                f"Hits: {session.hits} | Misses: {session.misses}"
            )
        if accuracy_label_ref["el"]:
            pct = int(session.accuracy * 100)
            accuracy_label_ref["el"].text = f"Accuracy: {pct}%"
        if streak_label_ref["el"]:
            streak_label_ref["el"].text = f"Streak: {session.streak}"
        if best_streak_label_ref["el"]:
            best_streak_label_ref["el"].text = f"Best: {session.best_streak}"

    def _next_note() -> None:
        if session.target_midi:
            ui.run_javascript(f"resetPianoKey({session.target_midi})")

        midi = session.pick_next()
        note_clef = session.choose_clef_for_note(midi)

        if staff_html_ref["el"]:
            staff_html_ref["el"].content = _render_note(midi, note_clef)
        if target_label_ref["el"]:
            target_label_ref["el"].text = midi_to_note_name(midi)
        ui.run_javascript(f"highlightPianoKeyPersist({midi}, '#42A5F5')")
        _update_display()

    def _on_note(note: int, velocity: int) -> None:
        if not active["value"]:
            return

        target = session.target_midi
        played_name = midi_to_note_name(note)

        if played_label_ref["el"]:
            played_label_ref["el"].text = played_name

        if note == target:
            session.hits += 1
            session.streak += 1
            if session.streak > session.best_streak:
                session.best_streak = session.streak
            ui.run_javascript(f"resetPianoKey({target})")
            ui.run_javascript(f"flashPianoKey({note}, '#4CAF50', 400)")
            if played_label_ref["el"]:
                played_label_ref["el"].classes(
                    replace="text-h5 font-bold text-green-600"
                )
            if feedback_label_ref["el"]:
                feedback_label_ref["el"].text = "✓ Correct!"
                feedback_label_ref["el"].classes(
                    replace="text-h6 font-bold q-ml-md text-green-600"
                )
            _update_display()
            _next_note()
        else:
            session.misses += 1
            session.streak = 0
            ui.run_javascript(f"flashPianoKey({note}, '#F44336', 600)")
            if played_label_ref["el"]:
                played_label_ref["el"].classes(
                    replace="text-h5 font-bold text-red-600"
                )
            if feedback_label_ref["el"]:
                target_name = midi_to_note_name(target)
                feedback_label_ref["el"].text = f"✗ Wrong — play {target_name}"
                feedback_label_ref["el"].classes(
                    replace="text-h6 font-bold q-ml-md text-red-600"
                )
            _update_display()

    def _start() -> None:
        if not midi.connected:
            ui.notify(
                "No MIDI device connected. Please select a device in the header first.",
                type="warning",
                position="top",
                close_button=True,
            )
            return

        pool = _build_note_pool(
            config["clef"],
            config["min_midi"],
            config["max_midi"],
            config["sharps_flats"],
        )
        if len(pool) < 2:
            ui.notify(
                "Note range too narrow — select a wider range.",
                type="warning",
                position="top",
            )
            return

        session.note_pool = list(pool)
        session.clef = config["clef"]
        session.hits = 0
        session.misses = 0
        session.streak = 0
        session.best_streak = 0
        session.recent_targets = []
        active["value"] = True

        if start_btn_ref["el"]:
            start_btn_ref["el"].visible = False
        if stop_btn_ref["el"]:
            stop_btn_ref["el"].visible = True
        if new_session_btn_ref["el"]:
            new_session_btn_ref["el"].visible = True
        if feedback_label_ref["el"]:
            feedback_label_ref["el"].text = ""
        if played_label_ref["el"]:
            played_label_ref["el"].text = "—"
            played_label_ref["el"].classes(
                replace="text-h5 font-bold text-grey-5"
            )

        _update_display()
        _next_note()
        midi.on_note_callback = _on_note

        # Set active zone on keyboard
        ui.run_javascript(
            f"setActiveZone({config['min_midi']}, {config['max_midi']})"
        )

    def _stop() -> None:
        active["value"] = False
        midi.on_note_callback = None
        if session.target_midi:
            ui.run_javascript(f"resetPianoKey({session.target_midi})")
        ui.run_javascript("clearActiveZone()")

        if start_btn_ref["el"]:
            start_btn_ref["el"].visible = True
        if stop_btn_ref["el"]:
            stop_btn_ref["el"].visible = False
        if target_label_ref["el"]:
            target_label_ref["el"].text = "—"
        if feedback_label_ref["el"]:
            total = session.total
            if total > 0:
                pct = int(session.accuracy * 100)
                feedback_label_ref["el"].text = (
                    f"Session done! {session.hits}/{total} ({pct}%) "
                    f"| Best streak: {session.best_streak}"
                )
                feedback_label_ref["el"].classes(
                    replace="text-h6 font-bold q-ml-md text-blue-800"
                )
        if staff_html_ref["el"]:
            staff_html_ref["el"].content = _render_empty_staff()

    def _new_session() -> None:
        _stop()
        session.hits = 0
        session.misses = 0
        session.streak = 0
        session.best_streak = 0
        _update_display()
        if feedback_label_ref["el"]:
            feedback_label_ref["el"].text = ""

    def _on_clef_change(e) -> None:
        config["clef"] = e.value
        clef_range = CLEF_RANGES.get(e.value, (60, 81))
        config["min_midi"] = clef_range[0]
        config["max_midi"] = clef_range[1]
        if staff_html_ref["el"] and not active["value"]:
            staff_html_ref["el"].content = _render_empty_staff()

    # ── UI Layout ────────────────────────────────────────────────

    with ui.row().classes("w-full gap-6"):
        # ── Config sidebar ───────────────────────────────────────
        with ui.card().classes("w-64 p-4 shrink-0"):
            ui.label("Configuration").classes("text-h6 text-blue-900 q-mb-sm")

            ui.label("Clef").classes("text-subtitle2 q-mt-sm")
            ui.select(
                options={
                    "treble": "Treble",
                    "bass": "Bass",
                    "grand": "Grand Staff",
                },
                value=DEFAULT_CLEF,
                on_change=_on_clef_change,
            ).props("dense outlined").classes("w-full")

            ui.label("Note Range").classes("text-subtitle2 q-mt-md")
            ui.label("(Adjusted per clef selection)").classes(
                "text-caption text-grey-6"
            )

            ui.separator().classes("q-my-sm")

            ui.label("Options").classes("text-subtitle2")
            ui.checkbox(
                "Include sharps/flats",
                value=DEFAULT_SHARPS_FLATS,
                on_change=lambda e: config.__setitem__(
                    "sharps_flats", e.value
                ),
            )
            ui.checkbox(
                "Include ledger lines",
                value=DEFAULT_LEDGER_LINES,
                on_change=lambda e: config.__setitem__(
                    "ledger_lines", e.value
                ),
            )

            ui.separator().classes("q-my-sm")

            ui.label("Key Signature").classes("text-subtitle2")
            _ks_options = {"none": "None (C major)"}
            _ks_options.update(
                {k: k + " major" for k in KEY_SIGNATURES if k != "C"}
            )

            def _on_keysig_change(e) -> None:
                config["key_signature"] = (
                    None if e.value == "none" else e.value
                )
                if staff_html_ref["el"] and not active["value"]:
                    staff_html_ref["el"].content = _render_empty_staff()

            ui.select(
                options=_ks_options,
                value="none",
                on_change=_on_keysig_change,
            ).props("dense outlined").classes("w-full")

        # ── Main practice area ───────────────────────────────────
        with ui.column().classes("flex-grow gap-4"):
            with ui.card().classes("w-full p-4"):
                ui.label("Sight-Reading Practice").classes("text-h6")
                ui.markdown(
                    "Notes appear on the staff. Play the correct key on your piano. "
                    "**Wait Mode:** the app waits for you — take your time!"
                )

                with ui.row().classes("items-center gap-4 q-my-sm"):
                    start_btn_ref["el"] = ui.button(
                        "Start Practice",
                        icon="play_arrow",
                        on_click=_start,
                    ).props("color=primary")
                    stop_btn_ref["el"] = ui.button(
                        "Stop", icon="stop", on_click=_stop
                    ).props("color=negative outline")
                    stop_btn_ref["el"].visible = False
                    new_session_btn_ref["el"] = ui.button(
                        "New Session", icon="refresh", on_click=_new_session
                    ).props("color=secondary outline")
                    new_session_btn_ref["el"].visible = False

                # Scoring row
                with ui.row().classes("items-center gap-6 q-my-sm"):
                    score_label_ref["el"] = ui.label(
                        "Hits: 0 | Misses: 0"
                    ).classes("text-subtitle1")
                    accuracy_label_ref["el"] = ui.label(
                        "Accuracy: 0%"
                    ).classes("text-subtitle1")
                    streak_label_ref["el"] = ui.label("Streak: 0").classes(
                        "text-subtitle1 text-orange-800"
                    )
                    best_streak_label_ref["el"] = ui.label("Best: 0").classes(
                        "text-subtitle1 text-purple-800"
                    )

                # Note feedback row
                with ui.row().classes("items-center gap-6 q-my-sm"):
                    with ui.column().classes("items-center gap-0"):
                        ui.label("Target").classes("text-caption text-grey-6")
                        target_label_ref["el"] = ui.label("—").classes(
                            "text-h5 font-bold text-blue-800"
                        )
                    with ui.column().classes("items-center gap-0"):
                        ui.label("You played").classes(
                            "text-caption text-grey-6"
                        )
                        played_label_ref["el"] = ui.label("—").classes(
                            "text-h5 font-bold text-grey-5"
                        )
                    feedback_label_ref["el"] = ui.label("").classes(
                        "text-h6 font-bold q-ml-md"
                    )

                # Staff display
                staff_html_ref["el"] = ui.html(_render_empty_staff()).classes(
                    "w-full q-my-md"
                )

    ui.run_javascript(FLASH_JS)

    # Keyboard
    ui.separator()
    ui.label("Your Keyboard").classes("text-h6")
    create_keyboard()
