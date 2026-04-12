"""Treble clef staff SVG renderer.

Renders a 5-line staff with treble clef and a single note at any position
from C4 (Middle C, ledger line below) to C6 (ledger line above).

Staff layout (bottom-up, line 1 = bottom):
  Line 5: F5   Space above 5: G5, A5, B5  (ledger for C6)
  Line 4: D5   Space 4-5: E5
  Line 3: B4   Space 3-4: C5
  Line 2: G4   Space 2-3: A4
  Line 1: E4   Space 1-2: F4
  Below line 1: D4 (space), C4 (ledger line)
"""

from __future__ import annotations

# ── Layout constants (SVG user-units) ────────────────────────────
STAFF_LEFT = 80  # leave room for clef
STAFF_RIGHT = 400
STAFF_WIDTH = STAFF_RIGHT - STAFF_LEFT
LINE_SPACING = 14  # distance between staff lines
STAFF_TOP = 40  # y of top line (line 5)
NOTE_RADIUS = 6
STEM_LENGTH = 42
LEDGER_HALF = 14  # half-length of ledger lines

# Y positions for the five staff lines (top to bottom = line 5 down to line 1)
STAFF_LINE_YS = [STAFF_TOP + i * LINE_SPACING for i in range(5)]
# line 5 = STAFF_LINE_YS[0], line 1 = STAFF_LINE_YS[4]

SVG_HEIGHT = 180
SVG_WIDTH = 450

# ── Note-to-position mapping ────────────────────────────────────

# Treble clef: each step is half a LINE_SPACING.
# Reference: B4 sits on line 3 (index 2 from top → y = STAFF_TOP + 2*LINE_SPACING).
# Steps above/below B4 shift by -LINE_SPACING/2 per step.

# Pitch class ordering (one step = one diatonic step)
_PITCH_CLASSES = ("C", "D", "E", "F", "G", "A", "B")
_NOTE_NAMES_SHARP = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)

# B4 reference: MIDI 71, on line 3 (index 2 → y = STAFF_TOP + 2*LINE_SPACING)
_B4_MIDI = 71
_B4_Y = STAFF_TOP + 2 * LINE_SPACING

# Diatonic MIDI numbers for one octave starting at C: 0,2,4,5,7,9,11
_DIATONIC_OFFSETS = (0, 2, 4, 5, 7, 9, 11)


def _midi_to_diatonic_steps_from_b4(midi: int) -> int | None:
    """Return diatonic steps above B4 (positive=up, negative=down).

    Returns None for sharps/flats (not renderable as natural notes on staff).
    """
    pc = midi % 12
    if pc not in _DIATONIC_OFFSETS:
        return None  # accidental — not supported yet

    octave = midi // 12 - 1
    # Diatonic index within octave
    note_idx = _DIATONIC_OFFSETS.index(pc)

    # B4: octave=4, note_idx=6
    b4_abs = 4 * 7 + 6  # absolute diatonic index of B4
    this_abs = octave * 7 + note_idx
    return this_abs - b4_abs


def midi_to_staff_y(midi: int) -> float | None:
    """Return the SVG y-coordinate for a note on the treble clef staff.

    Returns None for accidentals (sharps/flats).
    """
    steps = _midi_to_diatonic_steps_from_b4(midi)
    if steps is None:
        return None
    return _B4_Y - steps * (LINE_SPACING / 2)


def midi_to_note_name(midi: int) -> str:
    """Return e.g. 'C4', 'F#5' for a MIDI number."""
    return _NOTE_NAMES_SHARP[midi % 12] + str(midi // 12 - 1)


def needs_ledger_lines(midi: int) -> list[float]:
    """Return y-coordinates of ledger lines needed for this note."""
    y = midi_to_staff_y(midi)
    if y is None:
        return []

    ledgers: list[float] = []
    bottom_line_y = STAFF_LINE_YS[4]  # line 1
    top_line_y = STAFF_LINE_YS[0]  # line 5

    # Below staff
    ledger_y = bottom_line_y + LINE_SPACING
    while ledger_y <= y + 0.5:
        ledgers.append(ledger_y)
        ledger_y += LINE_SPACING

    # Above staff
    ledger_y = top_line_y - LINE_SPACING
    while ledger_y >= y - 0.5:
        ledgers.append(ledger_y)
        ledger_y -= LINE_SPACING

    return ledgers


# ── Treble clef symbol (simplified SVG path) ────────────────────

_TREBLE_CLEF_SVG = (
    '<g transform="translate({cx},{cy}) scale(0.35)" fill="#222" stroke="none">'
    '<path d="'
    "M 0 -70 "
    "C -2 -70, -14 -60, -14 -46 "
    "C -14 -28, 2 -16, 2 0 "
    "C 2 14, -10 22, -16 30 "
    "C -22 38, -22 52, -14 60 "
    "C -6 68, 8 64, 12 54 "
    "C 16 44, 10 34, 2 30 "
    "C -4 26, -10 28, -10 34 "
    "C -10 40, -4 42, 0 40 "
    "M 2 0 C 2 -10, 6 -40, 6 -56 "
    "C 6 -68, 2 -80, -2 -86 "
    "C -6 -92, -4 -100, 0 -100 "
    "C 4 -100, 8 -90, 8 -78 "
    "C 8 -62, 2 -34, 2 0 "
    "Z"
    '"/>'
    "</g>"
)


def _render_treble_clef(note_x: float) -> str:
    """Render the treble clef symbol. Positioned left of the staff."""
    # Treble clef is centred on G4 (line 2 = index 3)
    cx = STAFF_LEFT - 35
    cy = STAFF_LINE_YS[3]  # G4 line
    return _TREBLE_CLEF_SVG.replace("{cx}", f"{cx}").replace("{cy}", f"{cy}")


# ── Full SVG rendering ──────────────────────────────────────────


def render_staff_svg(
    target_midi: int | None = None,
    note_id: str = "staff-note",
) -> str:
    """Generate a treble clef staff SVG, optionally with a single note.

    Args:
        target_midi: MIDI number of the note to render (None = empty staff).
        note_id: DOM id for the note head element.
    """
    parts: list[str] = []
    parts.append(
        f'<svg id="treble-staff" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="width:100%;max-width:500px;height:auto;display:block;">'
    )

    # Background
    parts.append(
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" '
        f'fill="white" />'
    )

    # Staff lines
    for y in STAFF_LINE_YS:
        parts.append(
            f'<line x1="{STAFF_LEFT}" y1="{y}" x2="{STAFF_RIGHT}" y2="{y}" '
            f'stroke="#333" stroke-width="1.5" />'
        )

    # Treble clef
    note_x = (STAFF_LEFT + STAFF_RIGHT) / 2
    parts.append(_render_treble_clef(note_x))

    # Note
    if target_midi is not None:
        y = midi_to_staff_y(target_midi)
        if y is not None:
            # Ledger lines
            for ly in needs_ledger_lines(target_midi):
                parts.append(
                    f'<line x1="{note_x - LEDGER_HALF}" y1="{ly}" '
                    f'x2="{note_x + LEDGER_HALF}" y2="{ly}" '
                    f'stroke="#333" stroke-width="1.5" />'
                )

            # Note head (filled)
            parts.append(
                f'<ellipse id="{note_id}" cx="{note_x}" cy="{y}" '
                f'rx="{NOTE_RADIUS}" ry="{NOTE_RADIUS * 0.75}" '
                f'fill="#222" stroke="#222" stroke-width="1" '
                f'transform="rotate(-15 {note_x} {y})" />'
            )

            # Stem (up if below B4, down if on/above)
            steps = _midi_to_diatonic_steps_from_b4(target_midi)
            if steps is not None and steps >= 0:
                # Stem down (left side)
                parts.append(
                    f'<line x1="{note_x - NOTE_RADIUS + 1}" y1="{y}" '
                    f'x2="{note_x - NOTE_RADIUS + 1}" y2="{y + STEM_LENGTH}" '
                    f'stroke="#222" stroke-width="1.5" />'
                )
            else:
                # Stem up (right side)
                parts.append(
                    f'<line x1="{note_x + NOTE_RADIUS - 1}" y1="{y}" '
                    f'x2="{note_x + NOTE_RADIUS - 1}" y2="{y - STEM_LENGTH}" '
                    f'stroke="#222" stroke-width="1.5" />'
                )

            # Note name label (below SVG for debugging, small)
            name = midi_to_note_name(target_midi)
            parts.append(
                f'<text id="staff-note-label" x="{note_x}" y="{SVG_HEIGHT - 8}" '
                f'text-anchor="middle" font-size="11" fill="#999" '
                f'font-family="sans-serif" style="display:none;">{name}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)
