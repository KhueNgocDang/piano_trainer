"""Curriculum — all lessons in order.

Level 0: The Piano Keyboard (fundamentals)
Level 1: The Staff & Clefs (1.1–1.4)
"""

from __future__ import annotations

from app.keyboard.renderer import is_black_key
from app.lessons.models import Clef, Exercise, Lesson

# ══════════════════════════════════════════════════════════════════
# Level 0 — The Piano Keyboard
# ══════════════════════════════════════════════════════════════════

# White keys around Middle C for the first exercise: C4, D4, E4, F4, G4
_CENTER_KEYS = (60, 62, 64, 65, 67)

# One full octave of white keys: C4–B4
_ONE_OCTAVE_KEYS = (60, 62, 64, 65, 67, 69, 71)

# Two octaves: C3–B4
_TWO_OCTAVE_KEYS = tuple(m for m in range(48, 72) if not is_black_key(m))

LESSON_0_1 = Lesson(
    id="0.1",
    title="The Piano Keyboard",
    level=0,
    description="Learn how the piano keyboard is organized — white keys, black keys, and note names.",
    content_md="""\
## The Piano Keyboard

A full-size piano has **88 keys** — 52 white and 36 black. The keys repeat \
the same pattern of notes over and over, just higher or lower.

### The Musical Alphabet

Music uses only **7 natural note names**: **A B C D E F G**, then it repeats.

On the piano, these 7 notes are the **white keys**. They repeat across the \
entire keyboard from left (low) to right (high).

### Finding Your Way — The Black Key Pattern

The black keys come in groups of **2** and **3**:
- The group of **2** black keys sits between **C–D** and **D–E**
- The group of **3** black keys sits between **F–G**, **G–A**, and **A–B**

This pattern repeats across the whole keyboard. Use the black key groups as \
landmarks to find any white key!

### Middle C (C4)

**Middle C** is the white key just to the left of the group of 2 black keys \
closest to the center of the keyboard. It's your most important landmark note. \
On a MIDI keyboard, Middle C is note number **60**.

### Octave Numbers

Each time the notes repeat (C to B), it's one **octave**. We number them:
- **C1, C2, C3** … going up the keyboard
- **C4** = Middle C
- **C5, C6, C7, C8** … continuing to the top

So **A3** means "the A note in octave 3" (just below Middle C), and **G5** \
means "the G note in octave 5" (well above Middle C).

Look at the keyboard below — every white key is labeled with its note name \
and octave number!

### Exercise

Let's start simple. Play the 5 white keys around Middle C: **C4, D4, E4, F4, G4**. \
Find Middle C using the 2-black-key group, then play to the right.
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_CENTER_KEYS,
            num_notes=10,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id=None,  # always unlocked — this is the very first lesson
)

LESSON_0_2 = Lesson(
    id="0.2",
    title="One Octave — C to B",
    level=0,
    description="Learn all 7 white keys in one octave (C4 to B4).",
    content_md="""\
## One Octave: C4 to B4

Now let's learn the full set of 7 white keys in one octave.

Starting from **Middle C (C4)**, moving to the right:

| Key | Note Name | How to Find It |
|-----|-----------|----------------|
| 1   | **C4**    | Left of the 2-black-key group |
| 2   | **D4**    | Between the 2 black keys |
| 3   | **E4**    | Right of the 2-black-key group |
| 4   | **F4**    | Left of the 3-black-key group |
| 5   | **G4**    | Between 1st and 2nd of the 3 black keys |
| 6   | **A4**    | Between 2nd and 3rd of the 3 black keys |
| 7   | **B4**    | Right of the 3-black-key group |

After B4, the pattern starts over with **C5**.

### Exercise

Play all 7 notes in the C4 octave. Use the black key groups to find each one!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_ONE_OCTAVE_KEYS,
            num_notes=14,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="0.1",
)

LESSON_0_3 = Lesson(
    id="0.3",
    title="Two Octaves — C3 to B4",
    level=0,
    description="Expand to two octaves — recognize notes below and above Middle C.",
    content_md="""\
## Two Octaves: C3 to B4

Now let's expand your range. You'll play notes in **two octaves**: \
from **C3** (one octave below Middle C) to **B4**.

The notes are exactly the same — C D E F G A B — just in a lower octave. \
**C3** is the C key one group of 2-black-keys to the LEFT of Middle C.

### Tips
- Use the **black key groups** to orient yourself
- The note labels on the keyboard below show you exactly which key is which
- If you're unsure, look at the octave number: 3 = below Middle C, 4 = above

### Exercise

Notes from both octaves (C3–B4) will appear. Play the correct key!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_TWO_OCTAVE_KEYS,
            num_notes=14,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="0.2",
)

LEVEL_0_LESSONS: tuple[Lesson, ...] = (
    LESSON_0_1,
    LESSON_0_2,
    LESSON_0_3,
)

# ══════════════════════════════════════════════════════════════════
# Level 1 — The Staff & Clefs
# ══════════════════════════════════════════════════════════════════

# ── Note pools ───────────────────────────────────────────────────
# Treble line notes: E4(64), G4(67), B4(71), D5(74), F5(77)
_TREBLE_LINE_NOTES = (64, 67, 71, 74, 77)
# Treble space notes: F4(65), A4(69), C5(72), E5(76)
_TREBLE_SPACE_NOTES = (65, 69, 72, 76)
# All treble staff notes (no ledger lines): E4–F5
_TREBLE_STAFF_NOTES = tuple(m for m in range(64, 78) if not is_black_key(m))

# Bass line notes: G2(43), B2(47), D3(50), F3(53), A3(57)
_BASS_LINE_NOTES = (43, 47, 50, 53, 57)
# Bass space notes: A2(45), C3(48), E3(52), G3(55)
_BASS_SPACE_NOTES = (45, 48, 52, 55)
# All bass staff notes (no ledger lines): G2–A3
_BASS_STAFF_NOTES = tuple(m for m in range(43, 58) if not is_black_key(m))

# Middle C for grand staff lesson
_MIDDLE_C = (60,)

# ── Lesson 1.1 — The Staff ──────────────────────────────────────

LESSON_1_1 = Lesson(
    id="1.1",
    title="The Staff",
    level=1,
    description="Learn what a musical staff is — five lines and four spaces.",
    content_md="""\
## The Musical Staff

Music is written on a **staff** (also called a *stave*) — a set of **five horizontal lines** \
with **four spaces** between them.

Notes are placed **on** the lines or **in** the spaces. The higher a note sits on the staff, \
the higher it sounds.

### Lines (bottom to top)
In the treble clef, the lines from bottom to top represent:
- **E** – **G** – **B** – **D** – **F**
- Memory trick: **E**very **G**ood **B**oy **D**oes **F**ine

### Spaces (bottom to top)
The spaces spell out:
- **F** – **A** – **C** – **E**
- Memory trick: They spell **FACE**!

### Try it!
In the exercise below, notes will appear on the staff. Play the matching key on your piano. \
Start with just the **line notes** (E, G, B, D, F in the treble clef).
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_TREBLE_LINE_NOTES,
            num_notes=10,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="0.3",  # requires completing keyboard basics first
)

# ── Lesson 1.2 — Treble Clef ────────────────────────────────────

LESSON_1_2 = Lesson(
    id="1.2",
    title="Treble Clef",
    level=1,
    description="Meet the treble clef and learn all the notes on its staff.",
    content_md="""\
## The Treble Clef 𝄞

The **treble clef** (also called the *G clef*) is the most common clef. Its curl wraps \
around the **G line** (second line from bottom).

It's used for:
- Right hand piano parts
- Melody lines
- Guitar, violin, flute, and most higher-pitched instruments

### Line notes (bottom → top)
**E4 – G4 – B4 – D5 – F5**

### Space notes (bottom → top)
**F4 – A4 – C5 – E5** (they spell **FACE**)

### Exercise
Now you'll see notes from **both lines and spaces**. Play the correct key!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_TREBLE_STAFF_NOTES,
            num_notes=15,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="1.1",
)

# ── Lesson 1.3 — Bass Clef ──────────────────────────────────────

LESSON_1_3 = Lesson(
    id="1.3",
    title="Bass Clef",
    level=1,
    description="Learn the bass clef — the left hand's home on the piano.",
    content_md="""\
## The Bass Clef 𝄢

The **bass clef** (also called the *F clef*) has two dots that bracket the **F line** \
(fourth line from bottom, or second from top).

It's used for:
- Left hand piano parts
- Bass guitar, cello, trombone, and lower-pitched instruments

### Line notes (bottom → top)
**G2 – B2 – D3 – F3 – A3**
- Memory trick: **G**ood **B**oys **D**o **F**ine **A**lways

### Space notes (bottom → top)
**A2 – C3 – E3 – G3**
- Memory trick: **A**ll **C**ows **E**at **G**rass

### Exercise
Notes will appear on the **bass clef** staff. Play them on your piano!
""",
    exercises=(
        Exercise(
            clef=Clef.BASS,
            note_pool=_BASS_STAFF_NOTES,
            num_notes=15,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="1.2",
)

# ── Lesson 1.4 — Grand Staff ────────────────────────────────────

LESSON_1_4 = Lesson(
    id="1.4",
    title="The Grand Staff",
    level=1,
    description="Combine treble and bass clefs — and meet Middle C.",
    content_md="""\
## The Grand Staff

Piano music uses both clefs at once, forming the **grand staff**: the treble clef \
on top and the bass clef on the bottom, connected by a **brace** on the left.

### Middle C — The Bridge

**Middle C** (C4, MIDI 60) sits on a short **ledger line** between the two staves. \
It can be written in either clef:
- In the treble clef: one ledger line *below* the staff
- In the bass clef: one ledger line *above* the staff

Middle C is the most important landmark note — it connects the two worlds!

### Exercise
You'll see notes on the **grand staff**. Some will be on the treble staff, some on \
the bass staff. Read which clef the note is on and play the correct key!
""",
    exercises=(
        Exercise(
            clef=Clef.GRAND,
            note_pool=_TREBLE_STAFF_NOTES + _BASS_STAFF_NOTES + _MIDDLE_C,
            num_notes=20,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="1.3",
)

# ── All lessons in order ──────────────────────────────────────────

LEVEL_1_LESSONS: tuple[Lesson, ...] = (
    LESSON_1_1,
    LESSON_1_2,
    LESSON_1_3,
    LESSON_1_4,
)

ALL_LESSONS: tuple[Lesson, ...] = LEVEL_0_LESSONS + LEVEL_1_LESSONS

LESSON_BY_ID: dict[str, Lesson] = {lsn.id: lsn for lsn in ALL_LESSONS}
