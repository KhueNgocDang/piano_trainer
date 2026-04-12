"""Shared test fixtures."""

import pytest

from app.midi.bridge import MidiBridge


@pytest.fixture
def bridge():
    """Create a MidiBridge with no UI bindings for unit testing.

    The _log_container is None, so log entries accumulate in memory
    without attempting to render UI elements.
    """
    b = MidiBridge.__new__(MidiBridge)
    b.connected = False
    b.device_name = ""
    b.devices = []
    b.log_entries = []
    b.on_note_callback = None
    b._badge = None
    b._device_select = None
    b._log_container = None
    b._bridge = None
    return b
