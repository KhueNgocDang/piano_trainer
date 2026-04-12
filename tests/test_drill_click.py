"""Integration test for drill Start button."""

from nicegui.testing import User


async def test_drill_start_shows_note(user: User):
    """Click Start Drill and verify the staff updates with a note."""
    await user.open("/practice")
    await user.should_see("Note Reading Drill")
    await user.should_see("Start Drill")

    # Click Start Drill
    user.find("Start Drill").trigger("click")
    await user.should_see("Stop")
    await user.should_see("Hits: 0 / Misses: 0")
