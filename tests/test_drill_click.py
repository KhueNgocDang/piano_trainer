"""Integration test for drill Start button."""

from nicegui.testing import User


async def test_drill_start_without_midi_shows_warning(user: User):
    """Click Start Drill without MIDI device shows warning, drill does not start."""
    await user.open("/practice")
    await user.should_see("Note Reading Drill")
    await user.should_see("Start Drill")

    # Click Start Drill without a MIDI device connected
    user.find("Start Drill").trigger("click")
    # Should still see Start button (drill did not start)
    await user.should_see("Start Drill")
    # Warning notification shown
    await user.should_see("No MIDI device connected")
