"""SVG keyboard renderer with real-time MIDI highlighting support."""

from __future__ import annotations

from nicegui import ui

from app.keyboard.profiles import CASIO_PRIVIA, KeyboardProfile

# ── Layout constants (SVG user-units) ────────────────────────────
WHITE_KEY_WIDTH = 22
WHITE_KEY_HEIGHT = 140
WHITE_KEY_GAP = 1
WHITE_KEY_STRIDE = WHITE_KEY_WIDTH + WHITE_KEY_GAP  # 23
BLACK_KEY_WIDTH = 13
BLACK_KEY_HEIGHT = 90
LABEL_AREA_HEIGHT = 22

# ── Colours ──────────────────────────────────────────────────────
WHITE_DEFAULT = "#ffffff"
WHITE_ACTIVE = "#64B5F6"
BLACK_DEFAULT = "#1a1a1a"
BLACK_ACTIVE = "#1E88E5"
WHITE_STROKE = "#888888"
BLACK_STROKE = "#000000"
MIDDLE_C_FILL = "#FFD54F"
MIDDLE_C_STROKE = "#FFA000"
LABEL_COLOR = "#666666"

# ── Note helpers ─────────────────────────────────────────────────
BLACK_NOTE_OFFSETS = frozenset({1, 3, 6, 8, 10})  # C#, D#, F#, G#, A#
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
MIDDLE_C_MIDI = 60


def is_black_key(midi_note: int) -> bool:
    """Return True if the given MIDI note is a black key."""
    return (midi_note % 12) in BLACK_NOTE_OFFSETS


def midi_note_name(midi_note: int) -> str:
    """Return human-readable note name, e.g. 'C4' for MIDI 60."""
    return NOTE_NAMES[midi_note % 12] + str(midi_note // 12 - 1)


# ── Internal helpers ─────────────────────────────────────────────


def _build_white_key_map(profile: KeyboardProfile) -> dict[int, int]:
    """Return ``{midi_note: sequential_white_key_index}`` for all white keys."""
    wk_map: dict[int, int] = {}
    idx = 0
    for midi in range(profile.midi_start, profile.midi_end + 1):
        if not is_black_key(midi):
            wk_map[midi] = idx
            idx += 1
    return wk_map


# ── SVG generation ───────────────────────────────────────────────


def render_keyboard_svg(
    profile: KeyboardProfile = CASIO_PRIVIA,
    show_labels: bool = True,
) -> str:
    """Generate a complete SVG string for the keyboard.

    Each key ``<rect>`` carries ``id="piano-key-{midi}"`` plus ``data-default-color``
    and ``data-active-color`` attributes used by the client-side highlight JS.

    Args:
        profile: Keyboard profile defining the MIDI range.
        show_labels: If True, render note names (A3, B3, C4, …) on white keys.
    """
    wk_map = _build_white_key_map(profile)
    num_white = len(wk_map)
    total_w = num_white * WHITE_KEY_STRIDE - WHITE_KEY_GAP
    total_h = WHITE_KEY_HEIGHT + LABEL_AREA_HEIGHT

    parts: list[str] = []
    parts.append(
        f'<svg id="piano-keyboard" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {total_w} {total_h}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="width:100%;height:auto;display:block;">'
    )

    # ── White keys ───────────────────────────────────────────────
    for midi, idx in wk_map.items():
        x = idx * WHITE_KEY_STRIDE
        parts.append(
            f'<rect id="piano-key-{midi}" class="piano-white-key" '
            f'x="{x}" y="0" width="{WHITE_KEY_WIDTH}" height="{WHITE_KEY_HEIGHT}" '
            f'fill="{WHITE_DEFAULT}" stroke="{WHITE_STROKE}" stroke-width="1" '
            f'data-default-color="{WHITE_DEFAULT}" data-active-color="{WHITE_ACTIVE}" />'
        )

    # ── Black keys (drawn on top of white) ───────────────────────
    for midi in range(profile.midi_start, profile.midi_end + 1):
        if not is_black_key(midi):
            continue
        left_white = midi - 1
        right_white = midi + 1
        if left_white not in wk_map or right_white not in wk_map:
            continue
        lx = wk_map[left_white] * WHITE_KEY_STRIDE
        boundary = lx + WHITE_KEY_WIDTH + WHITE_KEY_GAP / 2
        bx = boundary - BLACK_KEY_WIDTH / 2
        parts.append(
            f'<rect id="piano-key-{midi}" class="piano-black-key" '
            f'x="{bx}" y="0" width="{BLACK_KEY_WIDTH}" height="{BLACK_KEY_HEIGHT}" '
            f'fill="{BLACK_DEFAULT}" stroke="{BLACK_STROKE}" stroke-width="1" '
            f'data-default-color="{BLACK_DEFAULT}" data-active-color="{BLACK_ACTIVE}" />'
        )

    # ── Middle C marker ──────────────────────────────────────────
    if MIDDLE_C_MIDI in wk_map:
        cx = wk_map[MIDDLE_C_MIDI] * WHITE_KEY_STRIDE + WHITE_KEY_WIDTH / 2
        cy = WHITE_KEY_HEIGHT - 12
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="5" '
            f'fill="{MIDDLE_C_FILL}" stroke="{MIDDLE_C_STROKE}" stroke-width="1" />'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 3}" text-anchor="middle" '
            f'font-size="7" font-weight="bold" fill="#333" '
            f'font-family="sans-serif">C4</text>'
        )

    # ── Note labels on white keys ──────────────────────────────────
    if show_labels:
        for midi, idx in wk_map.items():
            name = midi_note_name(midi)
            lx = idx * WHITE_KEY_STRIDE + WHITE_KEY_WIDTH / 2
            ly = WHITE_KEY_HEIGHT + 14
            # Use slightly larger font for C notes (octave landmarks)
            is_c = midi % 12 == 0
            font_size = 10 if is_c else 8
            weight = "bold" if is_c else "normal"
            color = "#333" if is_c else LABEL_COLOR
            parts.append(
                f'<text x="{lx}" y="{ly}" text-anchor="middle" '
                f'font-size="{font_size}" font-weight="{weight}" fill="{color}" '
                f'font-family="sans-serif">{name}</text>'
            )
    else:
        # Minimal labels: only C notes + A0
        for midi in range(profile.midi_start, profile.midi_end + 1):
            if midi % 12 == 0 and midi in wk_map:
                octave = midi // 12 - 1
                lx = wk_map[midi] * WHITE_KEY_STRIDE + WHITE_KEY_WIDTH / 2
                ly = WHITE_KEY_HEIGHT + 14
                parts.append(
                    f'<text x="{lx}" y="{ly}" text-anchor="middle" '
                    f'font-size="10" fill="{LABEL_COLOR}" '
                    f'font-family="sans-serif">C{octave}</text>'
                )
        if profile.midi_start == 21 and 21 in wk_map:
            lx = wk_map[21] * WHITE_KEY_STRIDE + WHITE_KEY_WIDTH / 2
            ly = WHITE_KEY_HEIGHT + 14
            parts.append(
                f'<text x="{lx}" y="{ly}" text-anchor="middle" '
                f'font-size="10" fill="{LABEL_COLOR}" '
                f'font-family="sans-serif">A0</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ── NiceGUI component ───────────────────────────────────────────


def create_keyboard(
    profile: KeyboardProfile = CASIO_PRIVIA,
    show_labels: bool = True,
) -> ui.html:
    """Add an interactive SVG keyboard to the current NiceGUI page."""
    svg = render_keyboard_svg(profile, show_labels=show_labels)
    return ui.html(svg).classes("w-full")
