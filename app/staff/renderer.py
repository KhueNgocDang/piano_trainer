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

# Mapping from chromatic pitch class to (diatonic base pitch class, accidental)
# When rendering a sharp: place note at the natural position + draw ♯
# When rendering a flat: place note at the natural above + draw ♭
_CHROMATIC_TO_DIATONIC: dict[int, tuple[int, str]] = {
    0: (0, ""),      # C
    1: (0, "sharp"), # C# → position of C + ♯
    2: (2, ""),      # D
    3: (2, "sharp"), # D# → position of D + ♯
    4: (4, ""),      # E
    5: (5, ""),      # F
    6: (5, "sharp"), # F# → position of F + ♯
    7: (7, ""),      # G
    8: (7, "sharp"), # G# → position of G + ♯
    9: (9, ""),      # A
    10: (9, "sharp"),# A# → position of A + ♯
    11: (11, ""),    # B
}

# ── Key signature definitions ────────────────────────────────────
# Each key maps to a set of pitch classes that are sharped/flatted.
# For sharp keys: the accidentals are sharps applied to these PCs.
# For flat keys: the accidentals are flats applied to these PCs.

KEY_SIGNATURES: dict[str, dict] = {
    "C":  {"accidentals": {},                                            "type": "none"},
    "G":  {"accidentals": {6: "sharp"},                                   "type": "sharp"},  # F#
    "D":  {"accidentals": {6: "sharp", 1: "sharp"},                       "type": "sharp"},  # F#, C#
    "A":  {"accidentals": {6: "sharp", 1: "sharp", 8: "sharp"},           "type": "sharp"},  # F#, C#, G#
    "E":  {"accidentals": {6: "sharp", 1: "sharp", 8: "sharp", 3: "sharp"}, "type": "sharp"},
    "F":  {"accidentals": {10: "flat"},                                   "type": "flat"},   # Bb
    "Bb": {"accidentals": {10: "flat", 3: "flat"},                        "type": "flat"},   # Bb, Eb
    "Eb": {"accidentals": {10: "flat", 3: "flat", 8: "flat"},             "type": "flat"},
    "Ab": {"accidentals": {10: "flat", 3: "flat", 8: "flat", 1: "flat"}, "type": "flat"},
}

# Order of sharps/flats in key signatures on the treble staff (MIDI PCs)
_SHARP_ORDER_TREBLE_Y_STEPS = [  # steps from B4 for F#, C#, G#, D#, A#, E#, B#
    (6, 4),   # F5 → 4 steps above B4
    (1, 0),   # C5 → on B4 wait no, C#5 → 1 step above B4
    (8, 5),   # G#5 → 5 steps above
    (3, 1),   # D#5 → 1 step above
    (10, 6),  # A#5 → 6 steps above (beyond normal but ok)
]

# Staff positions for key signature accidentals (diatonic steps from reference note)
# Treble clef (from B4): standard engraving positions
_KEYSIG_SHARP_STEPS_TREBLE = [4, 1, 5, 2, -1, 3, 0]   # F C G D A E B
_KEYSIG_FLAT_STEPS_TREBLE = [0, 3, -1, 2, -2, 1, -3]   # B E A D G C F

# Bass clef (from D3): standard engraving positions
_KEYSIG_SHARP_STEPS_BASS = [2, -1, 3, 0, -3, 1, -2]   # F C G D A E B
_KEYSIG_FLAT_STEPS_BASS = [-2, 1, -3, 0, -4, -1, -5]   # B E A D G C F


def _midi_to_diatonic_steps_from_b4(midi: int) -> int | None:
    """Return diatonic steps above B4 (positive=up, negative=down).

    Returns None for sharps/flats (not renderable as natural notes on staff).
    """
    pc = midi % 12
    if pc not in _DIATONIC_OFFSETS:
        return None  # accidental — use _midi_to_staff_info for accidentals

    octave = midi // 12 - 1
    # Diatonic index within octave
    note_idx = _DIATONIC_OFFSETS.index(pc)

    # B4: octave=4, note_idx=6
    b4_abs = 4 * 7 + 6  # absolute diatonic index of B4
    this_abs = octave * 7 + note_idx
    return this_abs - b4_abs


def _midi_to_staff_info_b4(midi: int) -> tuple[int, str]:
    """Return (diatonic_steps_from_B4, accidental) for any MIDI note.

    Always succeeds — handles both natural and accidental notes.
    accidental is '' for naturals, 'sharp' or 'flat'.
    """
    pc = midi % 12
    base_pc, acc = _CHROMATIC_TO_DIATONIC[pc]
    octave = midi // 12 - 1
    note_idx = _DIATONIC_OFFSETS.index(base_pc)
    b4_abs = 4 * 7 + 6
    this_abs = octave * 7 + note_idx
    return this_abs - b4_abs, acc


def midi_to_staff_y(midi: int) -> float | None:
    """Return the SVG y-coordinate for a note on the treble clef staff.

    Returns None for accidentals (sharps/flats) when called without accidental support.
    For accidental-aware positioning, use _midi_to_staff_y_ext().
    """
    steps = _midi_to_diatonic_steps_from_b4(midi)
    if steps is None:
        return None
    return _B4_Y - steps * (LINE_SPACING / 2)


def _midi_to_staff_y_ext(midi: int) -> tuple[float, str]:
    """Return (y, accidental) for any MIDI note on the treble clef staff.

    Always succeeds — handles accidentals by positioning at the base note.
    """
    steps, acc = _midi_to_staff_info_b4(midi)
    y = _B4_Y - steps * (LINE_SPACING / 2)
    return y, acc


def midi_to_note_name(midi: int) -> str:
    """Return e.g. 'C4', 'F#5' for a MIDI number."""
    return _NOTE_NAMES_SHARP[midi % 12] + str(midi // 12 - 1)


def needs_ledger_lines(midi: int) -> list[float]:
    """Return y-coordinates of ledger lines needed for this note."""
    y = midi_to_staff_y(midi)
    if y is None:
        # Try accidental-aware version
        y, _ = _midi_to_staff_y_ext(midi)

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


# ── Accidental glyph rendering ───────────────────────────────────

def _render_sharp_glyph(x: float, y: float) -> str:
    """Render a ♯ symbol at (x, y) as SVG."""
    # Simple sharp: two vertical lines + two horizontal lines
    return (
        f'<g transform="translate({x},{y})">'
        f'<line x1="-3" y1="-8" x2="-3" y2="8" stroke="#222" stroke-width="1.2"/>'
        f'<line x1="3" y1="-8" x2="3" y2="8" stroke="#222" stroke-width="1.2"/>'
        f'<line x1="-6" y1="-3" x2="6" y2="-5" stroke="#222" stroke-width="2"/>'
        f'<line x1="-6" y1="4" x2="6" y2="2" stroke="#222" stroke-width="2"/>'
        f'</g>'
    )


def _render_flat_glyph(x: float, y: float) -> str:
    """Render a ♭ symbol at (x, y) as SVG."""
    return (
        f'<g transform="translate({x},{y})">'
        f'<line x1="-2" y1="-12" x2="-2" y2="5" stroke="#222" stroke-width="1.5"/>'
        f'<path d="M -2,0 C 2,-2 6,-1 6,2 C 6,5 2,6 -2,5" '
        f'fill="none" stroke="#222" stroke-width="1.5"/>'
        f'</g>'
    )


def _render_keysig(
    parts: list[str],
    key_sig: str,
    ref_y: float,
    step_scale: float,
    is_bass: bool,
    start_x: float,
) -> float:
    """Render key signature accidentals on the staff. Returns the x after the last accidental."""
    if key_sig not in KEY_SIGNATURES or key_sig == "C":
        return start_x

    ks = KEY_SIGNATURES[key_sig]
    sig_type = ks["type"]
    accidentals = ks["accidentals"]

    if sig_type == "sharp":
        step_list = _KEYSIG_SHARP_STEPS_BASS if is_bass else _KEYSIG_SHARP_STEPS_TREBLE
        # Number of sharps = len(accidentals)
        n = len(accidentals)
        x = start_x
        for i in range(n):
            step = step_list[i]
            y = ref_y - step * (LINE_SPACING / 2)
            parts.append(_render_sharp_glyph(x, y))
            x += 10
        return x + 4
    elif sig_type == "flat":
        step_list = _KEYSIG_FLAT_STEPS_BASS if is_bass else _KEYSIG_FLAT_STEPS_TREBLE
        n = len(accidentals)
        x = start_x
        for i in range(n):
            step = step_list[i]
            y = ref_y - step * (LINE_SPACING / 2)
            parts.append(_render_flat_glyph(x, y))
            x += 10
        return x + 4

    return start_x


def _should_show_accidental(midi: int, key_sig: str | None) -> str:
    """Determine if a per-note accidental should be shown.

    Returns 'sharp', 'flat', or '' based on whether the note's accidental
    is already covered by the key signature.
    """
    pc = midi % 12
    _, acc = _CHROMATIC_TO_DIATONIC[pc]
    if not acc:
        return ""  # Natural note — no accidental needed

    if key_sig and key_sig in KEY_SIGNATURES:
        ks_accidentals = KEY_SIGNATURES[key_sig]["accidentals"]
        if pc in ks_accidentals:
            # The key signature already covers this accidental
            return ""

    return acc


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
    key_signature: str | None = None,
) -> str:
    """Generate a treble clef staff SVG, optionally with a single note.

    Args:
        target_midi: MIDI number of the note to render (None = empty staff).
        note_id: DOM id for the note head element.
        key_signature: Key name (e.g. 'G', 'F', 'Bb') or None for C major.
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

    # Key signature
    ks = key_signature or ""
    if ks:
        ref_y = _B4_Y  # B4 on line 3 of treble
        _render_keysig(parts, ks, ref_y, LINE_SPACING / 2, is_bass=False, start_x=STAFF_LEFT + 6)

    # Note
    if target_midi is not None:
        y, acc = _midi_to_staff_y_ext(target_midi)
        # Determine if per-note accidental is needed
        show_acc = _should_show_accidental(target_midi, key_signature) if acc else ""

        # Ledger lines
        for ly in needs_ledger_lines(target_midi):
            parts.append(
                f'<line x1="{note_x - LEDGER_HALF}" y1="{ly}" '
                f'x2="{note_x + LEDGER_HALF}" y2="{ly}" '
                f'stroke="#333" stroke-width="1.5" />'
            )

        # Accidental glyph (to the left of the note)
        if show_acc == "sharp":
            parts.append(_render_sharp_glyph(note_x - NOTE_RADIUS - 12, y))
        elif show_acc == "flat":
            parts.append(_render_flat_glyph(note_x - NOTE_RADIUS - 12, y))

        # Note head (filled)
        parts.append(
            f'<ellipse id="{note_id}" cx="{note_x}" cy="{y}" '
            f'rx="{NOTE_RADIUS}" ry="{NOTE_RADIUS * 0.75}" '
            f'fill="#222" stroke="#222" stroke-width="1" '
            f'transform="rotate(-15 {note_x} {y})" />'
        )

        # Stem (up if below B4, down if on/above)
        steps, _ = _midi_to_staff_info_b4(target_midi)
        if steps >= 0:
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


def _midi_to_staff_info_d3(midi: int) -> tuple[int, str]:
    """Return (diatonic_steps_from_D3, accidental) for any MIDI note."""
    pc = midi % 12
    base_pc, acc = _CHROMATIC_TO_DIATONIC[pc]
    octave = midi // 12 - 1
    note_idx = _DIATONIC_OFFSETS.index(base_pc)
    d3_abs = 3 * 7 + 1
    this_abs = octave * 7 + note_idx
    return this_abs - d3_abs, acc


def midi_to_bass_staff_y(midi: int) -> float | None:
    """Return the SVG y-coordinate for a note on the bass clef staff."""
    steps = _midi_to_diatonic_steps_from_d3(midi)
    if steps is None:
        return None
    return _D3_Y - steps * (LINE_SPACING / 2)


def _midi_to_bass_staff_y_ext(midi: int) -> tuple[float, str]:
    """Return (y, accidental) for any MIDI note on the bass clef staff."""
    steps, acc = _midi_to_staff_info_d3(midi)
    y = _D3_Y - steps * (LINE_SPACING / 2)
    return y, acc


def needs_ledger_lines_bass(midi: int) -> list[float]:
    """Return y-coordinates of ledger lines needed for a bass clef note."""
    y = midi_to_bass_staff_y(midi)
    if y is None:
        y, _ = _midi_to_bass_staff_y_ext(midi)

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
    key_signature: str | None = None,
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

    # Key signature
    ks = key_signature or ""
    if ks:
        ref_y = _D3_Y  # D3 on line 3 of bass
        _render_keysig(parts, ks, ref_y, LINE_SPACING / 2, is_bass=True, start_x=STAFF_LEFT + 6)

    note_x = (STAFF_LEFT + STAFF_RIGHT) / 2

    if target_midi is not None:
        y, acc = _midi_to_bass_staff_y_ext(target_midi)
        show_acc = _should_show_accidental(target_midi, key_signature) if acc else ""

        for ly in needs_ledger_lines_bass(target_midi):
            parts.append(
                f'<line x1="{note_x - LEDGER_HALF}" y1="{ly}" '
                f'x2="{note_x + LEDGER_HALF}" y2="{ly}" '
                f'stroke="#333" stroke-width="1.5" />'
            )

        # Accidental glyph
        if show_acc == "sharp":
            parts.append(_render_sharp_glyph(note_x - NOTE_RADIUS - 12, y))
        elif show_acc == "flat":
            parts.append(_render_flat_glyph(note_x - NOTE_RADIUS - 12, y))

        parts.append(
            f'<ellipse id="{note_id}" cx="{note_x}" cy="{y}" '
            f'rx="{NOTE_RADIUS}" ry="{NOTE_RADIUS * 0.75}" '
            f'fill="#222" stroke="#222" stroke-width="1" '
            f'transform="rotate(-15 {note_x} {y})" />'
        )

        # Stem direction: D3 is the reference on line 3
        steps, _ = _midi_to_staff_info_d3(target_midi)
        if steps >= 0:
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


def _midi_to_grand_staff_y_ext(midi: int, clef: str) -> tuple[float, str]:
    """Return (y, accidental) for any MIDI note on the grand staff."""
    if clef == "treble":
        steps, acc = _midi_to_staff_info_b4(midi)
        ref_y = GRAND_TREBLE_TOP + 2 * LINE_SPACING
        return ref_y - steps * (LINE_SPACING / 2), acc
    else:
        steps, acc = _midi_to_staff_info_d3(midi)
        ref_y = GRAND_BASS_TOP + 2 * LINE_SPACING
        return ref_y - steps * (LINE_SPACING / 2), acc


def needs_ledger_lines_grand(midi: int, clef: str) -> list[float]:
    """Return ledger line y-coordinates for a note on the grand staff."""
    y = midi_to_grand_staff_y(midi, clef)
    if y is None:
        y, _ = _midi_to_grand_staff_y_ext(midi, clef)

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
    key_signature: str | None = None,
) -> str:
    """Generate a grand staff SVG (treble + bass) with an optional note.

    Args:
        target_midi: MIDI number of the note to render.
        target_clef: Which staff the note belongs to ('treble' or 'bass').
        note_id: DOM id for the note head element.
        key_signature: Key name (e.g. 'G', 'F', 'Bb') or None for C major.
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

    # Key signatures on both staves
    ks = key_signature or ""
    if ks:
        treble_ref_y = GRAND_TREBLE_TOP + 2 * LINE_SPACING
        _render_keysig(parts, ks, treble_ref_y, LINE_SPACING / 2, is_bass=False, start_x=STAFF_LEFT + 6)
        bass_ref_y = GRAND_BASS_TOP + 2 * LINE_SPACING
        _render_keysig(parts, ks, bass_ref_y, LINE_SPACING / 2, is_bass=True, start_x=STAFF_LEFT + 6)

    note_x = (STAFF_LEFT + STAFF_RIGHT) / 2

    if target_midi is not None:
        y, acc = _midi_to_grand_staff_y_ext(target_midi, target_clef)
        show_acc = _should_show_accidental(target_midi, key_signature) if acc else ""

        for ly in needs_ledger_lines_grand(target_midi, target_clef):
            parts.append(
                f'<line x1="{note_x - LEDGER_HALF}" y1="{ly}" '
                f'x2="{note_x + LEDGER_HALF}" y2="{ly}" '
                f'stroke="#333" stroke-width="1.5" />'
            )

        # Accidental glyph
        if show_acc == "sharp":
            parts.append(_render_sharp_glyph(note_x - NOTE_RADIUS - 12, y))
        elif show_acc == "flat":
            parts.append(_render_flat_glyph(note_x - NOTE_RADIUS - 12, y))

        parts.append(
            f'<ellipse id="{note_id}" cx="{note_x}" cy="{y}" '
            f'rx="{NOTE_RADIUS}" ry="{NOTE_RADIUS * 0.75}" '
            f'fill="#222" stroke="#222" stroke-width="1" '
            f'transform="rotate(-15 {note_x} {y})" />'
        )

        # Stem direction based on position
        if target_clef == "treble":
            steps, _ = _midi_to_staff_info_b4(target_midi)
        else:
            steps, _ = _midi_to_staff_info_d3(target_midi)

        if steps >= 0:
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
