"""Integration tests for page routes using NiceGUI's User fixture."""

from nicegui.testing import User

from app.lessons import db as lesson_db


async def test_home_page_loads(user: User):
    await user.open("/")
    await user.should_see("Piano Trainer")
    await user.should_see("Home")


async def test_lessons_page_loads(user: User):
    await user.open("/lessons")
    await user.should_see("Lessons")


async def test_practice_page_loads(user: User):
    await user.open("/practice")
    await user.should_see("Practice")


async def test_flashcards_page_loads(user: User):
    await user.open("/flashcards")
    await user.should_see("Flash Cards")


async def test_progress_page_loads(user: User):
    await user.open("/progress")
    await user.should_see("Progress")


async def test_settings_page_loads(user: User):
    await user.open("/settings")
    await user.should_see("Settings")


async def test_home_has_navigation_links(user: User):
    await user.open("/")
    await user.should_see("Home")
    await user.should_see("Lessons")
    await user.should_see("Practice")
    await user.should_see("Flash Cards")
    await user.should_see("Progress")
    await user.should_see("Settings")


async def test_home_has_midi_badge(user: User):
    await user.open("/")
    await user.should_see("MIDI")


async def test_home_has_quick_start_buttons(user: User):
    await user.open("/")
    await user.should_see("Start Lessons")


# ── Lesson page integration tests ────────────────────────────────


async def test_lessons_page_shows_lesson_list(user: User):
    await user.open("/lessons")
    await user.should_see("Lesson 0.1")
    await user.should_see("The Piano Keyboard")


async def test_lessons_page_shows_level_1(user: User):
    await user.open("/lessons")
    await user.should_see("Lesson 1.1")
    await user.should_see("The Staff")


async def test_lessons_page_shows_locked_lessons(user: User):
    await user.open("/lessons")
    # Lesson 1.2 should be visible but locked (no progress)
    await user.should_see("Lesson 1.2")
    await user.should_see("Treble Clef")


async def test_lesson_detail_page_loads(user: User):
    await user.open("/lessons/1.1")
    await user.should_see("Lesson 1.1")
    await user.should_see("The Musical Staff")


async def test_lesson_detail_has_exercise(user: User):
    await user.open("/lessons/1.1")
    await user.should_see("Exercise")
    await user.should_see("Start Exercise")


async def test_lesson_detail_has_keyboard(user: User):
    await user.open("/lessons/1.1")
    await user.should_see("Your Keyboard")


async def test_lesson_detail_has_back_button(user: User):
    await user.open("/lessons/1.1")
    await user.should_see("Back to Lessons")


async def test_lesson_detail_not_found(user: User):
    await user.open("/lessons/99.99")
    await user.should_see("not found")


async def test_lesson_1_3_bass_clef(user: User):
    await user.open("/lessons/1.3")
    await user.should_see("Bass Clef")


async def test_lesson_1_4_grand_staff(user: User):
    await user.open("/lessons/1.4")
    await user.should_see("Grand Staff")


async def test_lesson_0_1_keyboard_basics(user: User):
    await user.open("/lessons/0.1")
    await user.should_see("The Piano Keyboard")
    await user.should_see("Musical Alphabet")


# ── Level 2 & 3 page integration tests ───────────────────────────


async def test_lessons_page_shows_level_headers(user: User):
    await user.open("/lessons")
    await user.should_see("Level 0")
    await user.should_see("Level 1")
    await user.should_see("Level 2")
    await user.should_see("Level 3")
    await user.should_see("Level 4")


async def test_lessons_page_shows_level_2(user: User):
    await user.open("/lessons")
    await user.should_see("Lesson 2.1")
    await user.should_see("Middle C, D, E")


async def test_lessons_page_shows_level_3(user: User):
    await user.open("/lessons")
    await user.should_see("Lesson 3.1")
    await user.should_see("Bass Clef")


async def test_lesson_2_1_detail(user: User):
    await user.open("/lessons/2.1")
    await user.should_see("Lesson 2.1")
    await user.should_see("Middle C, D, E")
    await user.should_see("Exercise")


async def test_lesson_2_4_ledger_lines(user: User):
    await user.open("/lessons/2.4")
    await user.should_see("Ledger Lines")


async def test_lesson_2_5_review(user: User):
    await user.open("/lessons/2.5")
    await user.should_see("Mixed Review")


async def test_lesson_3_1_detail(user: User):
    await user.open("/lessons/3.1")
    await user.should_see("Lesson 3.1")
    await user.should_see("Bass Clef")


async def test_lesson_3_5_review(user: User):
    await user.open("/lessons/3.5")
    await user.should_see("Mixed Review")


# ── Level 4 page integration tests ───────────────────────────────


async def test_lessons_page_shows_level_4(user: User):
    await user.open("/lessons")
    await user.should_see("Level 4")
    await user.should_see("Lesson 4.1")
    await user.should_see("Grand Staff Reading")


async def test_lesson_4_1_detail(user: User):
    await user.open("/lessons/4.1")
    await user.should_see("Lesson 4.1")
    await user.should_see("Grand Staff Reading")
    await user.should_see("Exercise")


async def test_lesson_4_2_landmarks(user: User):
    await user.open("/lessons/4.2")
    await user.should_see("Lesson 4.2")
    await user.should_see("Landmark Notes")


async def test_lessons_page_shows_level_4_header(user: User):
    await user.open("/lessons")
    await user.should_see("Both Clefs Together")
