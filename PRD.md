# Product Requirements Document (PRD)
## Piano Training — NiceGUI Sight-Reading Trainer

### 1. Overview

A NiceGUI-based desktop web application that teaches a complete beginner how to sight-read piano sheet music from scratch. The app connects to a CASIO Privia electric piano via USB-C MIDI and provides interactive, progressive lessons with real-time MIDI input feedback. The virtual keyboard dynamically matches the user's physical instrument.

**Reference:** [sightreading.training](https://sightreading.training/) — an open-source browser-based sight-reading practice tool.

**Why NiceGUI over Streamlit:** Streamlit's full-page rerun model adds unacceptable latency for real-time MIDI feedback. NiceGUI uses persistent WebSockets for instant server→client push, supports partial DOM updates, and can access the browser's Web MIDI API for zero-latency note detection.

---

### 2. Target User

- Complete beginner with zero sight-reading knowledge.
- Owns a CASIO Privia electric piano (88 keys) connected to a Linux PC via USB-C MIDI.
- Wants structured, progressive learning — not just random practice.

---

### 3. Goals

| # | Goal |
|---|------|
| G1 | Teach music notation fundamentals (staff, clefs, note names, rhythms) from zero. |
| G2 | Provide interactive exercises with real-time MIDI input from the CASIO Privia. |
| G3 | Track progress and adapt difficulty progressively. |
| G4 | Make practice engaging with immediate visual/audio feedback. |

---

### 4. Technical Stack

| Component | Technology |
|-----------|------------|
| UI Framework | **NiceGUI** (FastAPI + Vue.js, WebSocket-based) |
| MIDI Input (primary) | **Web MIDI API** via `ui.run_javascript()` — runs in browser, zero round-trip |
| MIDI Input (fallback) | `mido` + `python-rtmidi` server-side (for browsers without Web MIDI) |
| Music Notation Rendering | Custom SVG renderer (lightweight, inline, no external deps) |
| Virtual Keyboard | Dynamic SVG/HTML+CSS renderer driven by keyboard profile |
| Audio Playback | Web Audio API via JavaScript (browser-native, no server deps) |
| Data Persistence | SQLite via `aiosqlite` (async, local progress tracking) |
| Python Version | ≥ 3.13 |
| Package Manager | `uv` |

---

### 5. Core Features

#### 5.1 MIDI Connection Manager

- On page load, attempt **Web MIDI API** access in the browser (`navigator.requestMIDIAccess()`).
- List detected MIDI input devices in a dropdown selector.
- Display connection status badge: 🟢 Connected / 🔴 Disconnected.
- When a MIDI `note_on` event fires in the browser, emit it to the Python backend via NiceGUI's JavaScript↔Python bridge (`emitEvent`).
- **Fallback path:** If Web MIDI is unavailable (e.g., Firefox), fall back to server-side `mido` + `python-rtmidi` with a background `asyncio` task pushing notes over the WebSocket.
- Auto-reconnect on device disconnect/reconnect.

#### 5.2 Keyboard Profiles — Dynamic Instrument Rendering

The virtual keyboard matches the user's physical instrument. A **keyboard profile** defines the instrument's layout.

##### 5.2.1 Profile Data Model

```python
@dataclass
class KeyboardProfile:
    id: str                    # e.g. "casio_privia"
    name: str                  # e.g. "CASIO Privia (PX-S1100)"
    manufacturer: str          # e.g. "CASIO"
    total_keys: int            # e.g. 88
    midi_note_start: int       # e.g. 21 (A0)
    midi_note_end: int         # e.g. 108 (C8)
    octave_labels: bool        # Show octave markers on the keyboard
    key_width_px: float        # White key width for rendering
    key_height_white_px: float # White key height
    key_height_black_px: float # Black key height
```

##### 5.2.2 Built-In Profiles

| Profile ID | Name | Keys | MIDI Range | Notes |
|------------|------|------|------------|-------|
| `casio_privia` | CASIO Privia (88-key) | 88 | A0 (21) – C8 (108) | **Default.** All Privia models (PX-S1100, PX-870, etc.) |
| `generic_88` | Generic 88-key Piano | 88 | A0 (21) – C8 (108) | Standard full-size |
| `generic_76` | Generic 76-key | 76 | E1 (28) – G7 (103) | Mid-size keyboards |
| `generic_61` | Generic 61-key | 61 | C2 (36) – C7 (96) | Common practice keyboards |
| `generic_49` | Generic 49-key | 49 | C2 (36) – C6 (84) | Small MIDI controllers |

##### 5.2.3 Profile Selection

- Stored in user settings (SQLite). Persists across sessions.
- Selectable on the Settings page and during first-run onboarding.
- The virtual keyboard SVG re-renders when the profile changes.
- Future: auto-detect from MIDI device identity (`Device Inquiry` SysEx).

##### 5.2.4 Rendering Rules

- The virtual keyboard is rendered as an **inline SVG** in the browser.
- White keys are evenly spaced rectangles; black keys are narrower overlaid rectangles at the correct positions.
- The SVG width scales to fit the container (responsive).
- **Viewport/zoom:** For exercises targeting a small range (e.g., one octave around middle C), the keyboard can zoom into that range while still showing the full keyboard dimmed in the background.
- **Note labels:** All 52 white keys display their note name (A0, B0, C1, D1, …, C8) by default. C notes are rendered in bold with a larger font as octave landmarks; non-C notes use a smaller, lighter font. Labels can be toggled via the `show_labels` parameter.
- Middle C (C4, MIDI 60) is always marked with a subtle gold indicator.

#### 5.3 Lesson Module — Learn the Basics (Structured Curriculum)

A progressive curriculum that teaches sight-reading from absolute zero. Each lesson unlocks after the previous one is completed with ≥ 80% accuracy.

##### Level 0: The Piano Keyboard
- **Lesson 0.1 — The Piano Keyboard:** Musical alphabet (A–G), black key grouping pattern (2s and 3s), finding Middle C, octave numbering system. Exercise: play C4–G4.
- **Lesson 0.2 — One Octave:** All 7 white keys C4–B4 with finding tips (relative to black key groups). Exercise: play C4–B4.
- **Lesson 0.3 — Two Octaves:** Expand range to C3–B4 (14 white keys). Exercise: play C3–B4.

##### Level 0.5: Hand Placement
- **Lesson HP.1 — Finger Numbers & Hand Posture:** Introduce finger numbering (1=thumb → 5=pinky), curved finger posture, relaxed wrists, and proper hand shape.
- **Lesson HP.2 — Right Hand C Position:** Right hand on C4–G4 (thumb on C4). Exercise: play each finger in sequence and by name.
- **Lesson HP.3 — Left Hand C Position:** Left hand on C3–G3 (pinky on C3). Exercise: play each finger in sequence and by name.
- **Lesson HP.4 — Both Hands Together:** Parallel motion C–G with both hands. Introduces coordinating left and right simultaneously.

##### Level 1: The Staff & Clefs
- **Lesson 1.1 — The Staff:** Explain 5 lines, 4 spaces. Interactive SVG diagram. (Prerequisite: Lesson HP.4)
- **Lesson 1.2 — Treble Clef:** Introduce treble clef. Line notes (E-G-B-D-F), space notes (F-A-C-E). Mnemonics.
- **Lesson 1.3 — Bass Clef:** Introduce bass clef. Line notes (G-B-D-F-A), space notes (A-C-E-G). Mnemonics.
- **Lesson 1.4 — Grand Staff:** Combine treble + bass. Middle C as anchor point.

##### Level 2: Note Identification (Treble Clef)
- **Lesson 2.1 — Middle C, D, E:** Show notes on staff → user plays on piano. Keyboard highlights target zone.
- **Lesson 2.2 — F, G:** Expand range upward. Keyboard viewport zooms to relevant octave.
- **Lesson 2.3 — A, B, C (octave):** Complete one octave.
- **Lesson 2.4 — Ledger Lines (below staff):** Introduce notes below the staff.
- **Lesson 2.5 — Mixed Review:** Random notes from the full treble range.

##### Level 3: Note Identification (Bass Clef)
- **Lesson 3.1 — Middle C, B, A:** Notes around middle C in bass clef.
- **Lesson 3.2 — G, F:** Expand downward.
- **Lesson 3.3 — E, D, C:** Complete one octave down.
- **Lesson 3.4 — Ledger Lines (above staff):** Notes above the bass staff.
- **Lesson 3.5 — Mixed Review:** Random notes from the full bass range.

##### Level 4: Both Clefs Together
- **Lesson 4.1 — Grand Staff Reading:** Notes appear on either clef, user plays the correct key.
- **Lesson 4.2 — Landmark Notes:** Teach fast-recognition anchor notes (Middle C, Bass F, Treble G).

##### Level 5: Sharps, Flats & Key Signatures
- **Lesson 5.1 — Sharps & Flats:** Introduce accidentals visually and on keyboard.
- **Lesson 5.2 — Common Key Signatures:** C major, G major, F major, D major, Bb major.

##### Level 6: Rhythm Basics
- **Lesson 6.1 — Note Durations:** Whole, half, quarter, eighth notes. Visual comparison.
- **Lesson 6.2 — Time Signatures:** 4/4, 3/4, 2/4.
- **Lesson 6.3 — Rests:** Whole, half, quarter, eighth rests.

#### 5.4 Practice Module — Staff Note Reading

Inspired by sightreading.training's "Staff" mode:

- **Note Generator:** Randomly generate notes on the staff within a configurable range.
- **Modes:**
  - **Wait Mode:** App waits indefinitely for the user to play the correct note before advancing.
  - **Timed Mode:** Notes scroll across the staff at a configurable BPM. Missed notes count as errors.
- **Configuration Options (sidebar drawer):**
  - Clef selection: Treble / Bass / Grand Staff.
  - Note range: min/max pitch (visual slider mapped to keyboard profile range).
  - Number of simultaneous notes: 1 (single), 2 (intervals), 3+ (chords).
  - Include sharps/flats: on/off.
  - Include ledger lines: on/off.
- **Scoring:**
  - Track hits vs. misses in the current session.
  - Display running accuracy percentage.
  - Show streak counter for consecutive correct answers.

#### 5.5 Flash Cards Module

- Display a note on the staff → user plays the correct key on the piano.
- Display a note name → user plays the correct key on the piano.
- Display a key highlighted on the virtual keyboard → user names the note.
- Configurable: treble only, bass only, or both.

#### 5.6 Virtual Keyboard Display (Dynamic)

The keyboard is rendered dynamically based on the active **keyboard profile** (Section 5.2).

- **Full instrument rendering:** All keys of the physical instrument are drawn (e.g., 88 keys for CASIO Privia, A0–C8).
- **Real-time highlighting:** Keys light up instantly via JavaScript when MIDI `note_on` is received (no server round-trip for visual feedback).
- **Color coding:**
  - ⬜ Default white key / ⬛ Default black key.
  - 🟦 **Blue** = target note(s) the user should play.
  - 🟩 **Green** = correct note played.
  - 🟥 **Red** = wrong note played.
- **Note labels:** All 52 white keys labeled by default (A0, B0, C1, D1, …, C8). C notes in bold/larger font as octave landmarks. Togglable via `show_labels` parameter (default: on).
- **Active zone highlight:** During lessons, dim keys outside the exercise range and brighten the relevant section.
- **Responsive:** SVG scales to fit browser width. For 88 keys, allow horizontal scroll or zoom on smaller screens.
- **Middle C marker:** Always visible as an anchor reference.

#### 5.7 Progress Tracking

- **SQLite database** (async via `aiosqlite`) stores:
  - Lesson completion status and scores.
  - Practice session history (date, duration, accuracy, notes practiced).
  - Personal bests and streaks.
  - Active keyboard profile.
- **Dashboard page** showing:
  - Curriculum progress bar (lessons completed / total).
  - Accuracy trend graph over time (Plotly or ECharts via NiceGUI).
  - Most-missed notes (weakness analysis).
  - Total practice time.

---

### 6. UI / UX Design

#### 6.1 Page Layout

| Page | Route | Description |
|------|-------|-------------|
| **Home** | `/` | Welcome screen, MIDI status, quick-start buttons, progress summary. |
| **Lessons** | `/lessons` | Structured curriculum with lesson cards. Locked/unlocked states. |
| **Practice** | `/practice` | Free-form sight-reading practice (Staff mode). Configurable. |
| **Flash Cards** | `/flashcards` | Quick-fire note identification drills. |
| **Progress** | `/progress` | Dashboard with charts and statistics. |
| **Settings** | `/settings` | MIDI device, keyboard profile, audio, display preferences. |

#### 6.2 Navigation

- NiceGUI **left drawer** for page navigation (persistent, collapsible).
- **Header bar** shows: MIDI connection badge, keyboard profile name, session accuracy.
- Pages use NiceGUI's `@ui.page('/route')` decorator for client-side routing without full reloads.

#### 6.3 Music Notation Rendering

- Custom **inline SVG** renderer for staff, clef, and notes.
  - Treble clef, bass clef, and grand staff as SVG path data.
  - Notes positioned by computing staff line/space from MIDI note number.
  - Accidentals (♯, ♭, ♮) rendered as SVG text/paths.
- SVG is generated server-side in Python, pushed to the browser via NiceGUI's `ui.html()` or bound reactive element.
- Notes are large and clear (minimum 24px note head diameter).
- No external dependencies (no music21, no lilypond). Pure Python → SVG.

#### 6.4 Real-Time Feedback Architecture

```
[Browser: Web MIDI API]
    │  note_on event (< 1ms)
    ▼
[Browser: JavaScript handler]
    ├── Instantly update keyboard SVG (highlight key) ← NO server round-trip
    ├── Play audio feedback via Web Audio API
    └── Emit event to Python backend via WebSocket
            │
            ▼
      [Server: NiceGUI Python]
            ├── Validate note (correct/wrong)
            ├── Update score/progress
            └── Push next note to browser via WebSocket
                    │
                    ▼
              [Browser: update staff SVG, keyboard target]
```

**Key insight:** The keyboard highlight happens 100% client-side in JavaScript for zero latency. Only the game logic (is it correct? what's next?) goes through the server.

---

### 7. MIDI Integration Architecture

#### 7.1 Primary Path: Web MIDI API (Browser-Side)

```javascript
// Injected via ui.run_javascript() on page load
navigator.requestMIDIAccess().then(access => {
    for (let input of access.inputs.values()) {
        input.onmidimessage = (msg) => {
            const [status, note, velocity] = msg.data;
            if (status === 0x90 && velocity > 0) {  // note_on
                highlightKey(note, 'played');         // instant visual
                emitEvent('midi_note_on', { note, velocity });
            }
            if (status === 0x80 || (status === 0x90 && velocity === 0)) {
                unhighlightKey(note);
                emitEvent('midi_note_off', { note });
            }
        };
    }
});
```

- Works in Chromium-based browsers (Chrome, Edge, Brave).
- No Python MIDI library needed for the primary path.
- Device selection done in JavaScript, list pushed to NiceGUI UI.

#### 7.2 Fallback Path: Server-Side MIDI

For Firefox or other browsers without Web MIDI:

```
CASIO Privia → USB-C → Linux ALSA → python-rtmidi → mido → asyncio task → WebSocket → Browser
```

- `mido.open_input()` in an `asyncio` background task.
- Notes pushed to frontend via NiceGUI's server→client messaging.
- Slightly higher latency (~20–50ms) but fully functional.

#### 7.3 Note Mapping

| MIDI Note | Name | Keyboard Position |
|-----------|------|-------------------|
| 21 | A0 | First key (leftmost on 88-key) |
| 60 | C4 | Middle C |
| 108 | C8 | Last key (rightmost on 88-key) |

Standard formula: `note_name = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][midi % 12]`, `octave = (midi // 12) - 1`.

---

### 8. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Latency (note played → keyboard highlight) | < 10ms (client-side JS) |
| Latency (note played → correct/wrong feedback) | < 50ms (WebSocket round-trip) |
| Works offline | Yes (fully local, no internet needed) |
| Single-user | Yes (local desktop app) |
| Data storage | Local SQLite file |
| OS | Linux (primary), cross-platform possible |
| Browser | Chromium-based recommended (Web MIDI); Firefox supported via fallback |

---

### 9. Dependencies

```toml
[project]
dependencies = [
    "nicegui>=3.10",       # UI framework (FastAPI + Vue.js, WebSocket)
    "aiosqlite",           # Async SQLite for progress tracking
    "mido",                # MIDI message parsing (fallback path)
    "python-rtmidi",       # MIDI device access (fallback path)
]

[dependency-groups]
dev = [
    "pytest",              # Test runner
    "pytest-asyncio",      # Async test support
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

No heavy music libraries. Notation rendering is custom SVG. Audio is browser-native Web Audio API.

**Testing:** NiceGUI's `user_plugin` for fast integration tests (simulated browser, no Selenium). Unit tests for MIDI logic. Run with `uv run pytest tests/ -v`.

---

### 10. Incremental Development Timeline

Each milestone is a self-contained deliverable. After completing each one, development **pauses** for user verification before proceeding. Nothing from the next milestone is started until the current one passes review.

---

#### Milestone 1 — App Shell & MIDI Connection ✅ COMPLETE

**Goal:** Prove the technical foundation works — NiceGUI serves a page, the CASIO Privia is detected, and MIDI notes arrive in the browser.

**Deliverables:**
- [x] NiceGUI app boots and serves on `localhost:8080`.
- [x] Page layout with header bar and left-drawer navigation (placeholder pages).
- [x] Web MIDI API JavaScript injected on page load.
- [x] MIDI device dropdown populated with detected devices.
- [x] Connection status badge (green/red) in the header.
- [x] Console/debug panel shows raw MIDI `note_on`/`note_off` events as they arrive from the CASIO.
- [x] Test suite: 26 tests (6 MIDI JS, 11 bridge logic, 9 page integration).

**Verification checklist:**
> 1. Run the app → browser opens → you see the navigation drawer and header.
> 2. Connect CASIO Privia via USB-C → device appears in dropdown.
> 3. Select the device → status badge turns green.
> 4. Press any key on the piano → MIDI event appears on screen (note number + velocity).
> 5. Disconnect USB → status badge turns red.

---

#### Milestone 2 — Dynamic Keyboard Rendering ✅ COMPLETE

**Goal:** Render a full 88-key CASIO Privia keyboard as interactive SVG that lights up in real-time when you play.

**Deliverables:**
- [x] `KeyboardProfile` dataclass with CASIO Privia as the default profile.
- [x] SVG keyboard renderer: 88 keys (A0–C8), white + black keys at correct positions.
- [x] Octave labels (C1, C2, ... C8) below the keyboard.
- [x] Middle C (C4) marker.
- [x] Real-time key highlighting: pressing a key on the CASIO instantly highlights the SVG key (client-side JS, no server round-trip).
- [x] Keys return to default color on `note_off`.
- [x] Keyboard scales responsively to browser width.
- [x] Test suite: 43 new tests (69 total across profiles, renderer, SVG output, highlight JS, pages).

**Verification checklist:**
> 1. Open the app → 88-key keyboard is visible, properly proportioned.
> 2. Octave labels are correct (A0 on the left, C8 on the right).
> 3. Middle C is visually marked.
> 4. Play any key on the CASIO → corresponding SVG key highlights instantly (<10ms perceived).
> 5. Release the key → highlight disappears.
> 6. Play a fast scale → all keys highlight and release smoothly, no stuck keys.
> 7. Resize the browser window → keyboard scales without breaking.

---

#### Milestone 3 — Staff Notation Renderer (Treble Clef) ✅ COMPLETE

**Goal:** Render a treble clef staff with a single note, and validate whether the user played the correct note.

**Deliverables:**
- [x] Custom SVG renderer: 5-line staff with treble clef symbol.
- [x] Render a single note (filled/open note head) at the correct vertical position for any note in the treble clef range (C4–C6).
- [x] Ledger lines for notes below/above the staff (e.g., Middle C).
- [x] Note-to-staff-position mapping function (MIDI number → staff line/space in treble clef).
- [x] Generate a random target note → display on staff → wait for MIDI input → compare.
- [x] Correct: keyboard key flashes green, advance to next note.
- [x] Wrong: keyboard key flashes red, target key highlighted in blue.
- [x] Simple hit/miss counter displayed on screen.
- [x] Test suite: 52 new tests (121 total across staff renderer, drill state, bridge callback, pages).

**Verification checklist:**
> 1. A note appears on the treble clef staff — it looks like proper sheet music.
> 2. Middle C shows correctly on a ledger line below the staff.
> 3. Notes on lines and spaces are visually distinguishable.
> 4. Play the correct note on the CASIO → green flash → new note appears.
> 5. Play the wrong note → red flash → target remains, blue highlight shows correct key.
> 6. Hit/miss counter increments correctly.
> 7. Notes don't repeat excessively (reasonable randomness).

---

#### Milestone 4 — Lesson Framework, Level 0 (Keyboard Basics) & Level 1 (The Staff & Clefs) ✅ COMPLETE

**Goal:** Build the lesson system and deliver teaching content from absolute basics — which key is which note on the keyboard, then what a staff is, what clefs are, and where Middle C lives.

**Deliverables:**
- [x] Lesson data model: id, title, level, content (text + diagrams), exercises, unlock criteria.
- [x] Lesson list page (`/lessons`) showing all lessons with locked/unlocked states.
- [x] Lesson detail page with instructional content (text + inline SVG diagrams).
- [x] **Level 0 — The Piano Keyboard (3 lessons):**
  - [x] Lesson 0.1 — The Piano Keyboard: musical alphabet, black key pattern, Middle C, octave numbering. Exercise: play C4–G4.
  - [x] Lesson 0.2 — One Octave: all 7 white keys C4–B4. Exercise: play C4–B4.
  - [x] Lesson 0.3 — Two Octaves: C3–B4 (14 keys). Exercise: play C3–B4.
- [x] **Level 1 — The Staff & Clefs (4 lessons):**
  - [x] Lesson 1.1 — The Staff: interactive diagram labeling lines and spaces.
  - [x] Lesson 1.2 — Treble Clef: line/space note mnemonics + play-to-identify exercises.
  - [x] Lesson 1.3 — Bass Clef: same as 1.2 for bass clef (requires bass clef SVG renderer).
  - [x] Lesson 1.4 — Grand Staff: combined staff diagram, Middle C as bridge.
- [x] Prerequisite chain: 0.1 (unlocked) → 0.2 → 0.3 → 1.1 → 1.2 → 1.3 → 1.4.
- [x] Completion tracking: ≥ 80% accuracy on exercises to unlock next lesson.
- [x] SQLite database initialized on first run, stores lesson progress.
- [x] **Keyboard note labels:** all 52 white keys labeled (C notes bold/larger as landmarks).
- [x] Test suite: 193 total tests (models, curriculum, DB, keyboard labels, bass/grand renderer, exercise engine, Level 0 integration, pages).

**Verification checklist:**
> 1. `/lessons` page shows Level 0 and Level 1 lessons. Lesson 0.1 is unlocked, rest are locked.
> 2. Open Lesson 0.1 → educational content teaches the musical alphabet and keyboard layout.
> 3. Complete Lesson 0.1–0.3 exercises with ≥ 80% → Level 1 lessons unlock progressively.
> 4. Lesson 1.1 explains the staff clearly with a diagram.
> 5. Lesson 1.2 teaches treble clef notes → exercise asks you to play them.
> 6. Lesson 1.3 renders a bass clef staff correctly.
> 7. Lesson 1.4 shows a grand staff with Middle C connecting both.
> 8. All white keys on the virtual keyboard display their note name.
> 9. Close and reopen the app → progress is preserved (lessons stay unlocked).

---

#### Milestone 5 — Levels 2 & 3 (Note Identification — Treble & Bass) ✅ COMPLETE

**Goal:** User can identify and play individual notes across the full treble and bass clef ranges.

**Deliverables:**
- [x] Lessons 2.1–2.5: progressive treble clef note identification (B3→A5, including ledger lines and mixed review).
- [x] Lessons 3.1–3.5: progressive bass clef note identification (C4→E2, including ledger lines and mixed review).
- [x] Each lesson introduces 2–3 new notes, with exercises restricted to only learned notes (cumulative pools).
- [x] Keyboard "active zone" highlighting: `setActiveZone(min, max)` dims keys outside the exercise range; `clearActiveZone()` restores on finish.
- [x] Accuracy displayed per lesson attempt. Best score saved.
- [x] "Retry" button to redo a lesson.
- [x] Lessons page grouped by level with section headers.
- [x] Full prerequisite chain: 0.1→…→1.4→2.1→…→2.5→3.1→…→3.5 (17 lessons).
- [x] Test suite: 28 new tests (221 total).

**Verification checklist:**
> 1. Lesson 2.1 only asks for Middle C, D, E — no other notes appear.
> 2. Each subsequent lesson adds new notes while reviewing old ones.
> 3. The keyboard dims keys outside the active range for the current lesson.
> 4. By Lesson 2.5, any treble clef note (including ledger lines) can appear.
> 5. Bass clef lessons (3.1–3.5) work the same way for the bass range.
> 6. Best scores are saved per lesson.

---

#### Milestone 6 — Level 4 (Both Clefs) & Practice Mode ✅ COMPLETE

**Goal:** Grand staff reading + a free-form practice mode with configurable difficulty.

**Deliverables:**
- [x] Lesson 4.1 — Grand Staff Reading: notes randomly on treble or bass clef.
- [x] Lesson 4.2 — Landmark Notes: rapid-fire drill on Middle C, Bass F2, Treble G5.
- [x] Practice page (`/practice`) with configuration sidebar:
  - Clef selector (treble / bass / grand staff).
  - Note range (adjusted per clef selection).
  - Sharps/flats toggle.
  - Ledger lines toggle.
- [x] Wait Mode: infinite random notes, user plays at their own pace.
- [x] Session scoring: hits, misses, accuracy %, current streak, best streak.
- [x] Session resets on page load or "New Session" button.
- [x] Full prerequisite chain: 0.1→…→3.5→4.1→4.2 (19 lessons).
- [x] Test suite: 39 new tests (260 total).

**Verification checklist:**
> 1. Lesson 4.1 shows notes on both clefs — user must read which clef to decide the note.
> 2. Practice mode generates notes matching the selected configuration.
> 3. Changing clef/range immediately changes what notes appear.
> 4. Accuracy and streak counters work correctly.
> 5. Toggling sharps/flats on → accidentals appear on the staff and require correct sharp/flat key.

---

#### Milestone 7 — Flash Cards Module

**Goal:** Quick-fire note identification drills in multiple formats.

**Deliverables:**
- [ ] Flash Cards page (`/flashcards`) with mode selector:
  - **Staff → Piano:** Note shown on staff, user plays it.
  - **Name → Piano:** Note name shown (e.g., "F#4"), user plays it.
  - **Piano → Name:** Key highlighted on virtual keyboard, user types the name.
- [ ] Timer per card (configurable: off / 5s / 10s / 15s).
- [ ] Card count selector (10 / 20 / 50 / unlimited).
- [ ] End-of-set summary: total correct, accuracy, slowest/fastest response.
- [ ] Configurable: treble only, bass only, or both.

**Verification checklist:**
> 1. Each flash card mode works as described.
> 2. Timer counts down visually; auto-marks as miss if expired.
> 3. End-of-set summary shows accurate stats.
> 4. Clef filter actually restricts which notes appear.

---

#### Milestone 8 — Level 5 (Sharps, Flats, Key Signatures)

**Goal:** Teach accidentals and common key signatures.

**Deliverables:**
- [ ] Lesson 5.1 — Sharps & Flats: visual explanation of ♯/♭ on staff and keyboard.
- [ ] Exercises: staff shows a note with accidental → user plays the correct (sharp/flat) key.
- [ ] Lesson 5.2 — Key Signatures: C major, G major, F major, D major, Bb major.
- [ ] Key signature displayed at the beginning of the staff in exercises.
- [ ] Notes within a key signature exercise follow the signature (no accidental on each note).
- [ ] Practice mode updated: key signature selector added to config.

**Verification checklist:**
> 1. Lesson 5.1 clearly explains sharps and flats with before/after visuals.
> 2. Exercises require playing black keys — input is validated correctly.
> 3. Key signatures render at the start of the staff (sharps/flats on correct lines).
> 4. In key signature mode, an F in G major is automatically F# (no explicit accidental on the note).

---

#### Milestone 9 — Level 6 (Rhythm Basics) & Timed Practice Mode

**Goal:** Teach note durations and time signatures. Add timed/scrolling practice mode.

**Deliverables:**
- [ ] Lesson 6.1 — Note Durations: visual comparison (whole → eighth). Interactive diagrams.
- [ ] Lesson 6.2 — Time Signatures: 4/4, 3/4, 2/4 explained with beat counting.
- [ ] Lesson 6.3 — Rests: visual catalog of rest symbols.
- [ ] Timed Practice Mode on the Practice page:
  - Notes scroll left across the staff at configurable BPM.
  - Metronome click (Web Audio API).
  - Notes must be played in rhythm — early/late tolerance configurable.
  - Missed notes counted as errors.

**Verification checklist:**
> 1. Duration lessons show clear visual differences between whole, half, quarter, eighth.
> 2. Time signature lesson explains beats per measure with examples.
> 3. Timed mode: notes scroll smoothly at the configured BPM.
> 4. Metronome clicks are audible and in sync with the scroll.
> 5. Playing in time registers as a hit; playing late or missing registers as a miss.

---

#### Milestone 10 — Progress Dashboard

**Goal:** Comprehensive stats and progress visualization.

**Deliverables:**
- [ ] Progress page (`/progress`) with:
  - Curriculum progress bar (X of Y lessons completed).
  - Accuracy trend line chart (per-session accuracy over time).
  - Most-missed notes bar chart (top 10 problem notes).
  - Total practice time.
  - Streak records (best ever, current).
- [ ] Data sourced from SQLite (all sessions and lesson attempts logged).
- [ ] Charts via NiceGUI's built-in `ui.echart()` or `ui.plotly()`.

**Verification checklist:**
> 1. Progress page loads without errors and shows real data from your sessions.
> 2. Accuracy trend reflects actual session-by-session performance.
> 3. Most-missed notes match your experience (the notes you struggle with appear at the top).
> 4. Practice time is accumulated correctly across sessions.

---

#### Milestone 11 — Hand Placement (Level 0.5)

**Goal:** Teach proper hand posture, finger numbering, and basic C-position hand placement for both hands.

**Deliverables:**
- [ ] Lesson HP.1 — Finger Numbers & Hand Posture: visual diagrams of finger numbering (1=thumb → 5=pinky), curved finger shape, relaxed wrist position.
- [ ] Lesson HP.2 — Right Hand C Position: place right hand on C4–G4 (thumb on C4). Exercises: play each finger by number, identify which finger plays which note.
- [ ] Lesson HP.3 — Left Hand C Position: place left hand on C3–G3 (pinky on C3). Mirror exercises for the left hand.
- [ ] Lesson HP.4 — Both Hands Together: parallel C–G motion with both hands. Exercise: play matching fingers simultaneously.
- [ ] SVG hand diagram overlaid on/near the virtual keyboard showing finger placement.
- [ ] Prerequisite chain: 0.3 → HP.1 → HP.2 → HP.3 → HP.4 → 1.1.
- [ ] Keyboard active zone highlight matching the hand position (C3–G3 for left, C4–G4 for right).

**Verification checklist:**
> 1. Lesson HP.1 shows clear finger numbering diagrams for both hands.
> 2. HP.2 highlights C4–G4 and guides the user to place each right-hand finger.
> 3. HP.3 does the same for left hand on C3–G3.
> 4. HP.4 requires playing both hands — exercise tracks notes from both ranges.
> 5. Hand placement lessons fit naturally between Level 0 and Level 1.

---

#### Milestone 12 — Settings & Additional Keyboard Profiles

**Goal:** Settings page with keyboard profile management and user preferences.

**Deliverables:**
- [ ] Settings page (`/settings`) with:
  - MIDI device selector (mirrors header dropdown).
  - Keyboard profile selector (CASIO Privia, generic 88/76/61/49).
  - Note label toggle (show/hide on keyboard).
  - Audio feedback toggle.
- [ ] Switching keyboard profile dynamically re-renders the virtual keyboard (no reload).
- [ ] All 5 built-in profiles rendering correctly.
- [ ] Settings persisted in SQLite.

**Verification checklist:**
> 1. Changing to a 61-key profile → keyboard shrinks to 61 keys (C2–C7).
> 2. Changing back to CASIO Privia → full 88 keys again.
> 3. All settings persist after app restart.
> 4. Note labels toggle works on/off.

---

### 11. Open Questions

1. **Audio reference playback:** Should the app play a reference tone via Web Audio API when showing a target note? This helps ear training but may be distracting during sight-reading drills.
2. **Keyboard profile auto-detection:** MIDI `Device Inquiry` SysEx can identify the instrument model. Worth implementing, or just let the user pick from a list?
3. **Note queue / look-ahead display:** Instead of showing one note at a time, render a scrollable queue of upcoming notes on the staff (e.g., 4–8 notes visible). The leftmost note is the current target; when played correctly it slides off and the queue advances — similar to how real sheet music gives you a look-ahead. This encourages reading ahead (a core sight-reading skill). Configuration options: queue length (1 = current behaviour, 2–8 for look-ahead), scroll speed (for timed mode), and fade/opacity on future notes. This can be layered on top of the existing drill (Milestone 3) and timed practice (Milestone 9) without breaking either.

---

### 12. Success Criteria

- User can connect their CASIO Privia and see keys highlighted in the browser within < 10ms.
- The virtual keyboard accurately reflects the 88-key layout (A0–C8) of the CASIO Privia.
- A complete beginner can go from "what is a staff?" to confidently reading single notes on both clefs within 2–4 weeks of daily 15-min sessions.
- Practice mode provides unlimited, configurable reading exercises with scoring.
- Progress is persisted across sessions.
- Switching keyboard profiles dynamically re-renders the virtual keyboard without page reload.
