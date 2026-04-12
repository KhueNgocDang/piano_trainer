"""Tests for MidiBridge event handlers (logic only, no UI rendering)."""

from app.midi.bridge import MidiBridge, MidiEvent, MAX_LOG_ENTRIES


def test_midi_event_dataclass():
    e = MidiEvent(timestamp="12:00:00.000", message="test", event_type="info")
    assert e.timestamp == "12:00:00.000"
    assert e.message == "test"
    assert e.event_type == "info"


def test_bridge_on_note_on_logs_event(bridge: MidiBridge):
    bridge._on_note_on({"note": 60, "velocity": 100, "name": "C4"})
    assert len(bridge.log_entries) == 1
    assert "NOTE ON" in bridge.log_entries[0].message
    assert "C4" in bridge.log_entries[0].message
    assert "MIDI 60" in bridge.log_entries[0].message
    assert "vel=100" in bridge.log_entries[0].message
    assert bridge.log_entries[0].event_type == "note_on"


def test_bridge_on_note_off_logs_event(bridge: MidiBridge):
    bridge._on_note_off({"note": 60, "name": "C4"})
    assert len(bridge.log_entries) == 1
    assert "NOTE OFF" in bridge.log_entries[0].message
    assert "C4" in bridge.log_entries[0].message
    assert bridge.log_entries[0].event_type == "note_off"


def test_bridge_on_note_on_defaults_for_missing_keys(bridge: MidiBridge):
    bridge._on_note_on({})
    assert len(bridge.log_entries) == 1
    assert "MIDI 0" in bridge.log_entries[0].message
    assert "vel=0" in bridge.log_entries[0].message


def test_bridge_on_devices_updates_device_list(bridge: MidiBridge):
    devices = [
        {"id": "id1", "name": "CASIO USB-MIDI", "state": "connected"},
        {"id": "id2", "name": "Other Device", "state": "connected"},
    ]
    bridge._on_devices({"devices": devices})
    assert len(bridge.devices) == 2
    assert bridge.devices[0]["name"] == "CASIO USB-MIDI"
    assert bridge.devices[1]["name"] == "Other Device"


def test_bridge_on_devices_empty(bridge: MidiBridge):
    bridge._on_devices({"devices": []})
    assert bridge.devices == []
    assert any("No MIDI" in e.message for e in bridge.log_entries)


def test_bridge_on_status_connected(bridge: MidiBridge):
    bridge._on_status({"connected": True, "device": "CASIO USB-MIDI"})
    assert bridge.connected is True
    assert bridge.device_name == "CASIO USB-MIDI"


def test_bridge_on_status_disconnected(bridge: MidiBridge):
    bridge._on_status({"connected": True, "device": "CASIO"})
    bridge._on_status({"connected": False, "device": ""})
    assert bridge.connected is False
    assert bridge.device_name == ""


def test_bridge_on_status_error(bridge: MidiBridge):
    bridge._on_status(
        {"connected": False, "device": "", "error": "MIDI access denied"}
    )
    assert bridge.connected is False
    assert any("MIDI access denied" in e.message for e in bridge.log_entries)


def test_bridge_log_capped_at_max(bridge: MidiBridge):
    for i in range(MAX_LOG_ENTRIES + 50):
        bridge._on_note_on({"note": i % 128, "velocity": 64, "name": f"N{i}"})
    assert len(bridge.log_entries) == MAX_LOG_ENTRIES


def test_bridge_multiple_note_sequence(bridge: MidiBridge):
    """Simulate a short sequence of notes."""
    bridge._on_note_on({"note": 60, "velocity": 80, "name": "C4"})
    bridge._on_note_off({"note": 60, "name": "C4"})
    bridge._on_note_on({"note": 62, "velocity": 90, "name": "D4"})
    bridge._on_note_off({"note": 62, "name": "D4"})
    assert len(bridge.log_entries) == 4
    assert bridge.log_entries[0].event_type == "note_on"
    assert bridge.log_entries[1].event_type == "note_off"
    assert bridge.log_entries[2].event_type == "note_on"
    assert bridge.log_entries[3].event_type == "note_off"
