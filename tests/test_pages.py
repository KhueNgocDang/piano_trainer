"""Integration tests for page routes using NiceGUI's User fixture."""

from nicegui.testing import User


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
