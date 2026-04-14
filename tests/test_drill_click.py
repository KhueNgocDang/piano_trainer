"""Integration test for practice Start button."""

from nicegui.testing import User


async def test_practice_start_without_midi_shows_warning(user: User):
    """Click Start Practice without MIDI device shows warning, practice does not start."""
    await user.open("/practice")
    await user.should_see("Sight-Reading Practice")
    await user.should_see("Start Practice")

    # Click Start Practice without a MIDI device connected
    user.find("Start Practice").trigger("click")
    # Should still see Start button (practice did not start)
    await user.should_see("Start Practice")
    # Warning notification shown
    await user.should_see("No MIDI device connected")
