"""Staff SVG renderer — treble clef, bass clef, and grand staff.

Treble clef staff layout (bottom-up, line 1 = bottom):
  Line 5: F5   Space above 5: G5, A5, B5  (ledger for C6)
  Line 4: D5   Space 4-5: E5
  Line 3: B4   Space 3-4: C5
  Line 2: G4   Space 2-3: A4
  Line 1: E4   Space 1-2: F4
  Below line 1: D4 (space), C4 (ledger line)

Bass clef staff layout (bottom-up, line 1 = bottom):
  Line 5: A3   Space above 5: B3, C4 (ledger)
  Line 4: F3   Space 4-5: G3
  Line 3: D3   Space 3-4: E3
  Line 2: B2   Space 2-3: C3
  Line 1: G2   Space 1-2: A2
  Below line 1: F2, E2 (ledger)
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


# ══════════════════════════════════════════════════════════════════
# Bass clef support
# ══════════════════════════════════════════════════════════════════

# Bass clef reference: D3 sits on line 3.
# D3 = MIDI 50, diatonic absolute = 3*7+1 = 22
_D3_MIDI = 50
_D3_Y = (
    STAFF_TOP + 2 * LINE_SPACING
)  # same y-position as B4 in treble (line 3)


def _midi_to_diatonic_steps_from_d3(midi: int) -> int | None:
    """Return diatonic steps above D3 (positive=up, negative=down)."""
    pc = midi % 12
    if pc not in _DIATONIC_OFFSETS:
        return None
    octave = midi // 12 - 1
    note_idx = _DIATONIC_OFFSETS.index(pc)
    d3_abs = 3 * 7 + 1  # absolute diatonic index of D3
    this_abs = octave * 7 + note_idx
    return this_abs - d3_abs


def midi_to_bass_staff_y(midi: int) -> float | None:
    """Return the SVG y-coordinate for a note on the bass clef staff."""
    steps = _midi_to_diatonic_steps_from_d3(midi)
    if steps is None:
        return None
    return _D3_Y - steps * (LINE_SPACING / 2)


def needs_ledger_lines_bass(midi: int) -> list[float]:
    """Return y-coordinates of ledger lines needed for a bass clef note."""
    y = midi_to_bass_staff_y(midi)
    if y is None:
        return []

    ledgers: list[float] = []
    bottom_line_y = STAFF_LINE_YS[4]
    top_line_y = STAFF_LINE_YS[0]

    ledger_y = bottom_line_y + LINE_SPACING
    while ledger_y <= y + 0.5:
        ledgers.append(ledger_y)
        ledger_y += LINE_SPACING

    ledger_y = top_line_y - LINE_SPACING
    while ledger_y >= y - 0.5:
        ledgers.append(ledger_y)
        ledger_y -= LINE_SPACING

    return ledgers


# ── Bass clef symbol (simplified SVG path) ───────────────────────

_BASS_CLEF_SVG = (
    '<g transform="translate({cx},{cy}) scale(0.30)" fill="#222" stroke="none">'
    '<path d="'
    "M 0 0 "
    "C 0 -20, 18 -36, 36 -36 "
    "C 52 -36, 52 -12, 42 -2 "
    "C 32 8, 16 8, 8 0 "
    "C 2 -6, 8 -16, 16 -16 "
    "C 22 -16, 24 -12, 24 -8 "
    "C 24 -4, 20 0, 14 0 "
    "C 8 0, 2 -6, 0 0 Z"
    '"/>'
    '<circle cx="48" cy="-22" r="4" />'
    '<circle cx="48" cy="-10" r="4" />'
    "</g>"
)


def _render_bass_clef(staff_top: float = STAFF_TOP) -> str:
    """Render the bass clef symbol positioned left of the staff."""
    cx = STAFF_LEFT - 28
    # Bass clef sits between lines 4 and 3 (F3 line = line 4 from bottom = index 1)
    cy = staff_top + 1 * LINE_SPACING  # line 4 (F3)
    return _BASS_CLEF_SVG.replace("{cx}", f"{cx}").replace("{cy}", f"{cy}")


def render_bass_staff_svg(
    target_midi: int | None = None,
    note_id: str = "bass-staff-note",
) -> str:
    """Generate a bass clef staff SVG, optionally with a single note."""
    parts: list[str] = []
    parts.append(
        f'<svg id="bass-staff" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="width:100%;max-width:500px;height:auto;display:block;">'
    )
    parts.append(
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="white" />'
    )

    for y in STAFF_LINE_YS:
        parts.append(
            f'<line x1="{STAFF_LEFT}" y1="{y}" x2="{STAFF_RIGHT}" y2="{y}" '
            f'stroke="#333" stroke-width="1.5" />'
        )

    parts.append(_render_bass_clef())

    note_x = (STAFF_LEFT + STAFF_RIGHT) / 2

    if target_midi is not None:
        y = midi_to_bass_staff_y(target_midi)
        if y is not None:
            for ly in needs_ledger_lines_bass(target_midi):
                parts.append(
                    f'<line x1="{note_x - LEDGER_HALF}" y1="{ly}" '
                    f'x2="{note_x + LEDGER_HALF}" y2="{ly}" '
                    f'stroke="#333" stroke-width="1.5" />'
                )

            parts.append(
                f'<ellipse id="{note_id}" cx="{note_x}" cy="{y}" '
                f'rx="{NOTE_RADIUS}" ry="{NOTE_RADIUS * 0.75}" '
                f'fill="#222" stroke="#222" stroke-width="1" '
                f'transform="rotate(-15 {note_x} {y})" />'
            )

            # Stem direction: D3 is the reference on line 3
            steps = _midi_to_diatonic_steps_from_d3(target_midi)
            if steps is not None and steps >= 0:
                parts.append(
                    f'<line x1="{note_x - NOTE_RADIUS + 1}" y1="{y}" '
                    f'x2="{note_x - NOTE_RADIUS + 1}" y2="{y + STEM_LENGTH}" '
                    f'stroke="#222" stroke-width="1.5" />'
                )
            else:
                parts.append(
                    f'<line x1="{note_x + NOTE_RADIUS - 1}" y1="{y}" '
                    f'x2="{note_x + NOTE_RADIUS - 1}" y2="{y - STEM_LENGTH}" '
                    f'stroke="#222" stroke-width="1.5" />'
                )

            name = midi_to_note_name(target_midi)
            parts.append(
                f'<text id="bass-note-label" x="{note_x}" y="{SVG_HEIGHT - 8}" '
                f'text-anchor="middle" font-size="11" fill="#999" '
                f'font-family="sans-serif" style="display:none;">{name}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════
# Grand staff (treble + bass with brace)
# ══════════════════════════════════════════════════════════════════

GRAND_STAFF_HEIGHT = 320
GRAND_TREBLE_TOP = 30  # y of treble staff top line
GRAND_BASS_TOP = 190  # y of bass staff top line
GRAND_STAFF_GAP = GRAND_BASS_TOP - (
    GRAND_TREBLE_TOP + 4 * LINE_SPACING
)  # gap between staves


def _grand_treble_line_ys() -> list[float]:
    return [GRAND_TREBLE_TOP + i * LINE_SPACING for i in range(5)]


def _grand_bass_line_ys() -> list[float]:
    return [GRAND_BASS_TOP + i * LINE_SPACING for i in range(5)]


def midi_to_grand_staff_y(midi: int, clef: str) -> float | None:
    """Return SVG y-coordinate for a note on the grand staff.

    Args:
        midi: MIDI note number.
        clef: 'treble' or 'bass'.
    """
    if clef == "treble":
        steps = _midi_to_diatonic_steps_from_b4(midi)
        if steps is None:
            return None
        ref_y = GRAND_TREBLE_TOP + 2 * LINE_SPACING  # B4 on line 3
        return ref_y - steps * (LINE_SPACING / 2)
    else:
        steps = _midi_to_diatonic_steps_from_d3(midi)
        if steps is None:
            return None
        ref_y = GRAND_BASS_TOP + 2 * LINE_SPACING  # D3 on line 3
        return ref_y - steps * (LINE_SPACING / 2)


def needs_ledger_lines_grand(midi: int, clef: str) -> list[float]:
    """Return ledger line y-coordinates for a note on the grand staff."""
    y = midi_to_grand_staff_y(midi, clef)
    if y is None:
        return []

    if clef == "treble":
        line_ys = _grand_treble_line_ys()
    else:
        line_ys = _grand_bass_line_ys()

    ledgers: list[float] = []
    bottom_y = line_ys[4]
    top_y = line_ys[0]

    ly = bottom_y + LINE_SPACING
    while ly <= y + 0.5:
        ledgers.append(ly)
        ly += LINE_SPACING

    ly = top_y - LINE_SPACING
    while ly >= y - 0.5:
        ledgers.append(ly)
        ly -= LINE_SPACING

    return ledgers


def render_grand_staff_svg(
    target_midi: int | None = None,
    target_clef: str = "treble",
    note_id: str = "grand-staff-note",
) -> str:
    """Generate a grand staff SVG (treble + bass) with an optional note.

    Args:
        target_midi: MIDI number of the note to render.
        target_clef: Which staff the note belongs to ('treble' or 'bass').
        note_id: DOM id for the note head element.
    """
    parts: list[str] = []
    parts.append(
        f'<svg id="grand-staff" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_WIDTH} {GRAND_STAFF_HEIGHT}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="width:100%;max-width:500px;height:auto;display:block;">'
    )
    parts.append(
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{GRAND_STAFF_HEIGHT}" fill="white" />'
    )

    # Treble staff lines
    for y in _grand_treble_line_ys():
        parts.append(
            f'<line x1="{STAFF_LEFT}" y1="{y}" x2="{STAFF_RIGHT}" y2="{y}" '
            f'stroke="#333" stroke-width="1.5" />'
        )

    # Bass staff lines
    for y in _grand_bass_line_ys():
        parts.append(
            f'<line x1="{STAFF_LEFT}" y1="{y}" x2="{STAFF_RIGHT}" y2="{y}" '
            f'stroke="#333" stroke-width="1.5" />'
        )

    # Treble clef (centred on G4 = line 2 of treble = index 3)
    treble_lines = _grand_treble_line_ys()
    tcx = STAFF_LEFT - 35
    tcy = treble_lines[3]
    parts.append(
        _TREBLE_CLEF_SVG.replace("{cx}", f"{tcx}").replace("{cy}", f"{tcy}")
    )

    # Bass clef (on line 4 = index 1 of bass)
    bass_lines = _grand_bass_line_ys()
    bcx = STAFF_LEFT - 28
    bcy = bass_lines[1]
    parts.append(
        _BASS_CLEF_SVG.replace("{cx}", f"{bcx}").replace("{cy}", f"{bcy}")
    )

    # Brace (left vertical line connecting both staves)
    brace_top = treble_lines[0]
    brace_bottom = bass_lines[4]
    parts.append(
        f'<line x1="{STAFF_LEFT - 2}" y1="{brace_top}" '
        f'x2="{STAFF_LEFT - 2}" y2="{brace_bottom}" '
        f'stroke="#333" stroke-width="3" />'
    )

    # Barlines at left and right
    parts.append(
        f'<line x1="{STAFF_LEFT}" y1="{brace_top}" '
        f'x2="{STAFF_LEFT}" y2="{brace_bottom}" '
        f'stroke="#333" stroke-width="1.5" />'
    )

    # Middle C label between staves
    mid_y = (treble_lines[4] + bass_lines[0]) / 2
    parts.append(
        f'<text x="{STAFF_LEFT - 45}" y="{mid_y + 4}" '
        f'text-anchor="middle" font-size="9" fill="#999" '
        f'font-family="sans-serif">C4</text>'
    )

    note_x = (STAFF_LEFT + STAFF_RIGHT) / 2

    if target_midi is not None:
        y = midi_to_grand_staff_y(target_midi, target_clef)
        if y is not None:
            for ly in needs_ledger_lines_grand(target_midi, target_clef):
                parts.append(
                    f'<line x1="{note_x - LEDGER_HALF}" y1="{ly}" '
                    f'x2="{note_x + LEDGER_HALF}" y2="{ly}" '
                    f'stroke="#333" stroke-width="1.5" />'
                )

            parts.append(
                f'<ellipse id="{note_id}" cx="{note_x}" cy="{y}" '
                f'rx="{NOTE_RADIUS}" ry="{NOTE_RADIUS * 0.75}" '
                f'fill="#222" stroke="#222" stroke-width="1" '
                f'transform="rotate(-15 {note_x} {y})" />'
            )

            # Stem direction based on position
            if target_clef == "treble":
                steps = _midi_to_diatonic_steps_from_b4(target_midi)
            else:
                steps = _midi_to_diatonic_steps_from_d3(target_midi)

            if steps is not None and steps >= 0:
                parts.append(
                    f'<line x1="{note_x - NOTE_RADIUS + 1}" y1="{y}" '
                    f'x2="{note_x - NOTE_RADIUS + 1}" y2="{y + STEM_LENGTH}" '
                    f'stroke="#222" stroke-width="1.5" />'
                )
            else:
                parts.append(
                    f'<line x1="{note_x + NOTE_RADIUS - 1}" y1="{y}" '
                    f'x2="{note_x + NOTE_RADIUS - 1}" y2="{y - STEM_LENGTH}" '
                    f'stroke="#222" stroke-width="1.5" />'
                )

    parts.append("</svg>")
    return "\n".join(parts)
