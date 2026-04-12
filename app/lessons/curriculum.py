"""Level 1 curriculum — The Staff & Clefs.

Lessons 1.1–1.4 introduce the musical staff, treble clef, bass clef,
and grand staff. Each lesson has educational Markdown content and
interactive exercises.
"""

from __future__ import annotations

from app.keyboard.renderer import is_black_key
from app.lessons.models import Clef, Exercise, Lesson

# ── Note pools ───────────────────────────────────────────────────
# Treble line notes: E4(64), G4(67), B4(71), D5(74), F5(77)
_TREBLE_LINE_NOTES = (64, 67, 71, 74, 77)
# Treble space notes: F4(65), A4(69), C5(72), E5(76)
_TREBLE_SPACE_NOTES = (65, 69, 72, 76)
# All treble staff notes (no ledger lines): E4–F5
_TREBLE_STAFF_NOTES = tuple(
    m for m in range(64, 78) if not is_black_key(m)
)

# Bass line notes: G2(43), B2(47), D3(50), F3(53), A3(57)
_BASS_LINE_NOTES = (43, 47, 50, 53, 57)
# Bass space notes: A2(45), C3(48), E3(52), G3(55)
_BASS_SPACE_NOTES = (45, 48, 52, 55)
# All bass staff notes (no ledger lines): G2–A3
_BASS_STAFF_NOTES = tuple(
    m for m in range(43, 58) if not is_black_key(m)
)

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
    prerequisite_id=None,  # always unlocked
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

# ── All Level 1 lessons in order ─────────────────────────────────

LEVEL_1_LESSONS: tuple[Lesson, ...] = (
    LESSON_1_1,
    LESSON_1_2,
    LESSON_1_3,
    LESSON_1_4,
)

ALL_LESSONS: tuple[Lesson, ...] = LEVEL_1_LESSONS

LESSON_BY_ID: dict[str, Lesson] = {lsn.id: lsn for lsn in ALL_LESSONS}
