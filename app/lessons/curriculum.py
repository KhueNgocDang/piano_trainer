"""Curriculum — all lessons in order.

Level 0: The Piano Keyboard (fundamentals)
Level 1: The Staff & Clefs (1.1–1.4)
Level 2: Note Identification — Treble Clef (2.1–2.5)
Level 3: Note Identification — Bass Clef (3.1–3.5)
Level 4: Both Clefs Together (4.1–4.2)
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

# ══════════════════════════════════════════════════════════════════
# Level 2 — Note Identification (Treble Clef)
# ══════════════════════════════════════════════════════════════════

# Progressive note pools (cumulative — each lesson adds new notes)
_L2_POOL_1 = (60, 62, 64)  # C4, D4, E4
_L2_POOL_2 = (60, 62, 64, 65, 67)  # + F4, G4
_L2_POOL_3 = (60, 62, 64, 65, 67, 69, 71, 72)  # + A4, B4, C5
_L2_POOL_4 = (
    59,
    60,
    62,
    64,
    65,
    67,
    69,
    71,
    72,
    74,
    76,
    77,
)  # + B3, D5, E5, F5
_L2_POOL_5 = (
    59,
    60,
    62,
    64,
    65,
    67,
    69,
    71,
    72,
    74,
    76,
    77,
    79,
    81,
)  # + G5, A5

LESSON_2_1 = Lesson(
    id="2.1",
    title="Middle C, D, E",
    level=2,
    description="Start reading treble clef — identify C4, D4, and E4 on the staff.",
    content_md="""\
## Reading Notes: Middle C, D, E

Now that you know the staff and the treble clef, let's start reading actual notes!

We'll begin with three notes near **Middle C**:

| Note | MIDI | Position on Staff |
|------|------|-------------------|
| **C4** | 60 | On a **ledger line** just below the staff |
| **D4** | 62 | In the **space** just below line 1 |
| **E4** | 64 | On **line 1** (the bottom line) |

### Tips
- **C4** has its own short line — this is called a *ledger line*
- **D4** floats in the space between C4's ledger line and line 1
- **E4** sits right on the bottom line of the staff

Look at where the note sits on the staff, then play the matching key!

### Exercise
A note will appear on the treble staff. Play the correct key on your piano. \
Only C4, D4, and E4 will appear.
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L2_POOL_1,
            num_notes=10,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="1.4",
)

LESSON_2_2 = Lesson(
    id="2.2",
    title="Adding F and G",
    level=2,
    description="Expand your range upward — add F4 and G4.",
    content_md="""\
## Adding F and G

Two more notes on the treble staff:

| Note | MIDI | Position on Staff |
|------|------|-------------------|
| **F4** | 65 | In the **space** between lines 1 and 2 |
| **G4** | 67 | On **line 2** |

### How to tell them apart
- **F4** floats in the first space (just above line 1 / E4)
- **G4** sits on line 2 — the line that the treble clef curls around!

You now know 5 notes: **C4, D4, E4, F4, G4** — the first five notes of the C major scale.

### Exercise
Notes from C4 through G4 will appear. Play each one!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L2_POOL_2,
            num_notes=10,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="2.1",
)

LESSON_2_3 = Lesson(
    id="2.3",
    title="A, B, and High C — One Octave",
    level=2,
    description="Complete the octave from C4 to C5.",
    content_md="""\
## Completing the Octave: A, B, C5

Three more notes bring you to a full octave:

| Note | MIDI | Position on Staff |
|------|------|-------------------|
| **A4** | 69 | In the **space** between lines 2 and 3 |
| **B4** | 71 | On **line 3** (the middle line) |
| **C5** | 72 | In the **space** between lines 3 and 4 |

### Pattern recognition
- Spaces spell **F–A–C–E** from bottom to top
- Lines go **E–G–B–D–F** from bottom to top
- B4 on line 3 is the exact middle of the staff!

You can now read one full octave on the treble staff: **C4 → C5**.

### Exercise
Any note from C4 to C5 may appear. Play them all!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L2_POOL_3,
            num_notes=12,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="2.2",
)

LESSON_2_4 = Lesson(
    id="2.4",
    title="Ledger Lines & Upper Staff",
    level=2,
    description="Extend your range — notes below and at the top of the staff.",
    content_md="""\
## Ledger Lines & The Full Staff

Notes can go **beyond** the five staff lines using short extra lines called \
**ledger lines**. You've already been playing C4, which sits on a ledger line!

### New notes below the staff
| Note | MIDI | Position |
|------|------|----------|
| **B3** | 59 | Space **below** C4's ledger line |

### New notes at the top of the staff
| Note | MIDI | Position |
|------|------|----------|
| **D5** | 74 | On **line 4** |
| **E5** | 76 | In the **space** between lines 4 and 5 |
| **F5** | 77 | On **line 5** (the top line) |

### Tips
- B3 is the note just below Middle C — look for notes sitting below the ledger line
- D5 and F5 are on the top two lines of the staff
- E5 is in the space between them

Your range now spans from B3 to F5 — almost the entire treble staff!

### Exercise
Notes from B3 to F5 will appear. Watch for notes above and below the main staff lines!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L2_POOL_4,
            num_notes=15,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="2.3",
)

LESSON_2_5 = Lesson(
    id="2.5",
    title="Treble Clef — Mixed Review",
    level=2,
    description="Random notes across the full treble clef range, including ledger lines.",
    content_md="""\
## Treble Clef Mixed Review

Time to put it all together! You'll see notes from the **full treble clef range**, \
including ledger lines above and below the staff.

### Two new notes above the staff
| Note | MIDI | Position |
|------|------|----------|
| **G5** | 79 | **Space** just above line 5 |
| **A5** | 81 | On a **ledger line** above the staff |

### Your full range: B3 → A5
That's **14 natural notes** spanning nearly two octaves!

### Strategy tips
- Start from landmark notes you know well: **Middle C (C4)**, **B4 (line 3)**, **F5 (line 5)**
- Count steps from the nearest landmark
- Notes above/below the staff always use ledger lines — count them carefully

### Exercise
Random notes from B3 to A5. This is the most challenging treble clef drill yet!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L2_POOL_5,
            num_notes=20,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="2.4",
)

LEVEL_2_LESSONS: tuple[Lesson, ...] = (
    LESSON_2_1,
    LESSON_2_2,
    LESSON_2_3,
    LESSON_2_4,
    LESSON_2_5,
)

# ══════════════════════════════════════════════════════════════════
# Level 3 — Note Identification (Bass Clef)
# ══════════════════════════════════════════════════════════════════

# Progressive note pools (starting from top of bass staff, expanding downward)
_L3_POOL_1 = (57, 59, 60)  # A3, B3, C4
_L3_POOL_2 = (53, 55, 57, 59, 60)  # + F3, G3
_L3_POOL_3 = (48, 50, 52, 53, 55, 57, 59, 60)  # + C3, D3, E3
_L3_POOL_4 = (
    41,
    43,
    45,
    47,
    48,
    50,
    52,
    53,
    55,
    57,
    59,
    60,
)  # + F2, G2, A2, B2
_L3_POOL_5 = (40, 41, 43, 45, 47, 48, 50, 52, 53, 55, 57, 59, 60)  # + E2

LESSON_3_1 = Lesson(
    id="3.1",
    title="Middle C, B, A (Bass Clef)",
    level=3,
    description="Start reading bass clef — C4, B3, and A3 around the top of the staff.",
    content_md="""\
## Bass Clef: Starting from the Top

Welcome to the bass clef! We'll start from notes you already know — near **Middle C** — \
but now reading them in the **bass clef** 𝄢.

| Note | MIDI | Position on Bass Staff |
|------|------|------------------------|
| **C4** | 60 | On a **ledger line** just above the staff |
| **B3** | 59 | In the **space** just above line 5 |
| **A3** | 57 | On **line 5** (the top line) |

### Key difference from treble clef
In treble clef, C4 was below the staff. In bass clef, C4 is **above** the staff! \
Same note, same key on the piano, but written in a different position.

### Exercise
Notes will appear on the **bass clef** staff. Play C4, B3, or A3 as shown!
""",
    exercises=(
        Exercise(
            clef=Clef.BASS,
            note_pool=_L3_POOL_1,
            num_notes=10,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="2.5",
)

LESSON_3_2 = Lesson(
    id="3.2",
    title="Adding G and F (Bass Clef)",
    level=3,
    description="Expand downward — add G3 and F3.",
    content_md="""\
## Bass Clef: G3 and F3

Two more notes, moving down the bass staff:

| Note | MIDI | Position on Bass Staff |
|------|------|------------------------|
| **G3** | 55 | In the **space** between lines 4 and 5 |
| **F3** | 53 | On **line 4** — the line the bass clef's dots surround! |

### Bass clef landmark
**F3 on line 4** is the bass clef's anchor note — just like G4 on line 2 is the \
treble clef's anchor. The two dots of the 𝄢 symbol sit above and below this line.

### Exercise
Notes from F3 to C4 will appear on the bass staff.
""",
    exercises=(
        Exercise(
            clef=Clef.BASS,
            note_pool=_L3_POOL_2,
            num_notes=10,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="3.1",
)

LESSON_3_3 = Lesson(
    id="3.3",
    title="E, D, C — Bass Clef Center",
    level=3,
    description="Learn the middle of the bass staff — E3, D3, and C3.",
    content_md="""\
## Bass Clef: E3, D3, C3

The center of the bass staff:

| Note | MIDI | Position on Bass Staff |
|------|------|------------------------|
| **E3** | 52 | In the **space** between lines 3 and 4 |
| **D3** | 50 | On **line 3** (the middle line) |
| **C3** | 48 | In the **space** between lines 2 and 3 |

### Mnemonics reminder
- Bass clef spaces (bottom to top): **A–C–E–G** → *All Cows Eat Grass*
- Bass clef lines (bottom to top): **G–B–D–F–A** → *Good Boys Do Fine Always*

D3 on line 3 is the exact middle of the bass staff — a good landmark!

### Exercise
Notes from C3 to C4 — the full octave on the bass staff.
""",
    exercises=(
        Exercise(
            clef=Clef.BASS,
            note_pool=_L3_POOL_3,
            num_notes=12,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="3.2",
)

LESSON_3_4 = Lesson(
    id="3.4",
    title="Bottom of Staff & Ledger Lines",
    level=3,
    description="Reach the bottom of the bass staff and learn a ledger line below.",
    content_md="""\
## Bottom of the Bass Staff

Let's complete the bass staff and go below it:

### Remaining staff notes
| Note | MIDI | Position on Bass Staff |
|------|------|------------------------|
| **B2** | 47 | On **line 2** |
| **A2** | 45 | In the **space** between lines 1 and 2 |
| **G2** | 43 | On **line 1** (the bottom line) |

### Ledger line below the staff
| Note | MIDI | Position |
|------|------|----------|
| **F2** | 41 | In the **space** just below line 1 |

### Tips
- G2 on line 1 is the lowest note directly on the staff
- F2 is just below — it floats in the space under line 1
- Count carefully from D3 (line 3) or G2 (line 1) as landmarks

### Exercise
Notes from F2 to C4 — nearly the full bass range!
""",
    exercises=(
        Exercise(
            clef=Clef.BASS,
            note_pool=_L3_POOL_4,
            num_notes=15,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="3.3",
)

LESSON_3_5 = Lesson(
    id="3.5",
    title="Bass Clef — Mixed Review",
    level=3,
    description="Random notes across the full bass clef range, including ledger lines.",
    content_md="""\
## Bass Clef Mixed Review

Time for the full bass clef range! You'll see notes from **E2 to C4**, \
including ledger lines above and below the staff.

### One more note below the staff
| Note | MIDI | Position |
|------|------|----------|
| **E2** | 40 | On a **ledger line** below the staff |

### Your full bass range: E2 → C4
That's **13 natural notes** spanning nearly two octaves!

### Strategy tips
- Use **landmarks**: D3 (line 3), F3 (line 4, bass clef anchor), G2 (line 1)
- **Above the staff**: B3 (space above line 5), C4 (ledger line)
- **Below the staff**: F2 (space below line 1), E2 (ledger line)
- Count steps up or down from the nearest landmark

### Exercise
Random notes from E2 to C4. The complete bass clef challenge!
""",
    exercises=(
        Exercise(
            clef=Clef.BASS,
            note_pool=_L3_POOL_5,
            num_notes=20,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="3.4",
)

LEVEL_3_LESSONS: tuple[Lesson, ...] = (
    LESSON_3_1,
    LESSON_3_2,
    LESSON_3_3,
    LESSON_3_4,
    LESSON_3_5,
)

# ══════════════════════════════════════════════════════════════════
# Level 4 — Both Clefs Together
# ══════════════════════════════════════════════════════════════════

# Grand staff: combine full treble + bass ranges
_L4_GRAND_POOL = _L2_POOL_5 + _L3_POOL_5
# Remove duplicates (C4/60 may appear in both), keep tuple
_L4_GRAND_POOL = tuple(sorted(set(_L4_GRAND_POOL)))

# Landmark notes for rapid-fire drill: Middle C, Bass F2, Treble G5
_L4_LANDMARKS = (60, 41, 79)  # C4, F2, G5

LESSON_4_1 = Lesson(
    id="4.1",
    title="Grand Staff Reading",
    level=4,
    description="Read notes on both clefs — treble and bass together on the grand staff.",
    content_md="""\
## Grand Staff Reading

You've mastered reading treble clef and bass clef separately. Now it's time \
to read them **together** on the **grand staff**!

### How it works
- A note will appear on either the treble staff or the bass staff
- You must first identify **which clef** the note is on
- Then read the note name and play it on your piano

### Key differences to watch for
The same staff position means **different notes** depending on the clef:
- **Line 1** in treble = **E4**, but line 1 in bass = **G2**
- **Line 3** in treble = **B4**, but line 3 in bass = **D3**
- **Middle C** (C4) appears on a ledger line in both clefs

### Strategy
1. Look at which staff the note is on (top = treble, bottom = bass)
2. Use your landmark notes: E4 (treble line 1), B4 (treble line 3), \
D3 (bass line 3), G2 (bass line 1)
3. Count steps from the nearest landmark

### Exercise
Random notes will appear on the grand staff. Play them all!
""",
    exercises=(
        Exercise(
            clef=Clef.GRAND,
            note_pool=_L4_GRAND_POOL,
            num_notes=20,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="3.5",
)

LESSON_4_2 = Lesson(
    id="4.2",
    title="Landmark Notes",
    level=4,
    description="Rapid-fire drill on the most important anchor notes across both clefs.",
    content_md="""\
## Landmark Notes

**Landmark notes** are anchor points you can recognize instantly — without \
counting steps from other notes. The faster you recognize these, the faster \
you can read all other notes by counting from the nearest landmark.

### The Big Three Landmarks

| Landmark | MIDI | Clef | Position |
|----------|------|------|----------|
| **Middle C (C4)** | 60 | Both | Ledger line between staves |
| **F2** | 41 | Bass | Space below line 1 |
| **G5** | 79 | Treble | Space above line 5 |

### Additional landmarks to internalize
- **G4** (MIDI 67) — treble line 2, the treble clef curls around it
- **F3** (MIDI 53) — bass line 4, the bass clef dots surround it
- **B4** (MIDI 71) — treble line 3 (middle of treble staff)
- **D3** (MIDI 50) — bass line 3 (middle of bass staff)

### Exercise
Only the three main landmarks will appear. Identify them as fast as you can!
""",
    exercises=(
        Exercise(
            clef=Clef.GRAND,
            note_pool=_L4_LANDMARKS,
            num_notes=15,
            pass_threshold=0.80,
        ),
    ),
    prerequisite_id="4.1",
)

LEVEL_4_LESSONS: tuple[Lesson, ...] = (
    LESSON_4_1,
    LESSON_4_2,
)

# ═════════════════════════════════════════════════════════════════
# Level 5 — Sharps, Flats & Key Signatures
# ═════════════════════════════════════════════════════════════════

# Note pools that include accidentals (black keys)
_L5_SHARPS_TREBLE = (
    60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71,  # C4–B4 chromatic
    72, 73, 74, 75, 76, 77, 78, 79,  # C5–G5 chromatic
)
_L5_SHARPS_BASS = (
    40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,  # E2–Eb3 chromatic
    52, 53, 54, 55, 56, 57, 58, 59, 60,  # E3–C4 chromatic
)

# G major note pool (F# included, naturals on other notes)
_L5_G_MAJOR_TREBLE = (60, 62, 64, 66, 67, 69, 71, 72, 74, 76, 78, 79)  # C D E F# G A B ...
_L5_F_MAJOR_TREBLE = (60, 62, 64, 65, 67, 69, 70, 72, 74, 76, 77, 79)  # C D E F G A Bb ...
_L5_D_MAJOR_TREBLE = (61, 62, 64, 66, 67, 69, 71, 73, 74, 76, 78, 79)  # C# D E F# G A B ...
_L5_Bb_MAJOR_TREBLE = (60, 62, 63, 65, 67, 69, 70, 72, 74, 75, 77, 79)  # C D Eb F G A Bb ...

LESSON_5_1 = Lesson(
    id="5.1",
    title="Sharps & Flats",
    level=5,
    description="Learn to read and play sharp (♯) and flat (♭) notes on the staff.",
    content_md="""\
## Sharps & Flats

A **sharp (♯)** raises a note by one half step (one key to the right on the piano).
A **flat (♭)** lowers a note by one half step (one key to the left on the piano).

### On the Staff
When a note has an accidental, the ♯ or ♭ symbol appears **directly to the left** \
of the note head. This tells you to play the black key instead of the white key.

### Common Accidentals
| Written | Means | MIDI Example |
|---------|-------|-------------|
| F♯ | Play the black key between F and G | F♯4 = MIDI 66 |
| B♭ | Play the black key between A and B | B♭4 = MIDI 70 |
| C♯ | Play the black key between C and D | C♯4 = MIDI 61 |
| E♭ | Play the black key between D and E | E♭4 = MIDI 63 |
| G♯ | Play the black key between G and A | G♯4 = MIDI 68 |

### Enharmonic Equivalents
The same black key can have two names:
- F♯ = G♭ (same key!)
- C♯ = D♭ (same key!)

### Exercise
Notes with sharps and flats will appear on the staff. Play the correct key, \
including the black keys!
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L5_SHARPS_TREBLE,
            num_notes=15,
            pass_threshold=0.75,
        ),
        Exercise(
            clef=Clef.BASS,
            note_pool=_L5_SHARPS_BASS,
            num_notes=10,
            pass_threshold=0.70,
        ),
    ),
    prerequisite_id="4.2",
)

LESSON_5_2 = Lesson(
    id="5.2",
    title="Key Signatures",
    level=5,
    description="Understand key signatures and how they affect which notes are sharp or flat.",
    content_md="""\
## Key Signatures

A **key signature** appears at the beginning of each staff line, right after the clef. \
It tells you which notes are **always** sharp or flat throughout the piece — so you \
don't need an accidental on every single note.

### How Key Signatures Work
- The sharps or flats in the key signature apply to **every occurrence** of that note.
- If the key signature has F♯, then **every F** in the piece is played as F♯.
- No extra ♯ symbol is written next to each F — the key signature does it for you.

### Common Key Signatures

| Key | Accidentals | Sharps/Flats |
|-----|------------|--------------|
| **C major** | None | — |
| **G major** | F♯ | 1 sharp |
| **D major** | F♯, C♯ | 2 sharps |
| **F major** | B♭ | 1 flat |
| **B♭ major** | B♭, E♭ | 2 flats |

### Reading with Key Signatures
1. Look at the key signature after the clef
2. Remember which notes are affected
3. When you see one of those notes, play the sharp/flat version

### Exercises
Practice playing in different keys! The key signature is shown at the beginning \
of the staff. Notes within the key follow the signature — no extra accidentals.
""",
    exercises=(
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L5_G_MAJOR_TREBLE,
            num_notes=12,
            pass_threshold=0.75,
            key_signature="G",
        ),
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L5_F_MAJOR_TREBLE,
            num_notes=12,
            pass_threshold=0.75,
            key_signature="F",
        ),
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L5_D_MAJOR_TREBLE,
            num_notes=12,
            pass_threshold=0.75,
            key_signature="D",
        ),
        Exercise(
            clef=Clef.TREBLE,
            note_pool=_L5_Bb_MAJOR_TREBLE,
            num_notes=12,
            pass_threshold=0.75,
            key_signature="Bb",
        ),
    ),
    prerequisite_id="5.1",
)

LEVEL_5_LESSONS: tuple[Lesson, ...] = (
    LESSON_5_1,
    LESSON_5_2,
)

# ── All lessons in order ──────────────────────────────────────────

ALL_LESSONS: tuple[Lesson, ...] = (
    LEVEL_0_LESSONS
    + LEVEL_1_LESSONS
    + LEVEL_2_LESSONS
    + LEVEL_3_LESSONS
    + LEVEL_4_LESSONS
    + LEVEL_5_LESSONS
)

LESSON_BY_ID: dict[str, Lesson] = {lsn.id: lsn for lsn in ALL_LESSONS}
