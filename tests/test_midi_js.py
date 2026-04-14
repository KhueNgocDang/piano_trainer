"""Tests for MIDI JavaScript generation."""

from app.midi.midi_js import get_midi_js


def test_get_midi_js_injects_bridge_id():
    js = get_midi_js(42)
    assert "const BRIDGE_ID = 42;" in js


def test_get_midi_js_contains_midi_api_call():
    js = get_midi_js(1)
    assert "navigator.requestMIDIAccess" in js


def test_get_midi_js_contains_note_handlers():
    js = get_midi_js(1)
    assert "midi-note-on" in js
    assert "midi-note-off" in js
    assert "midi-status" in js
    assert "midi-devices" in js


def test_get_midi_js_contains_note_name_conversion():
    js = get_midi_js(1)
    assert "midiToName" in js
    assert "NOTE_NAMES" in js


def test_get_midi_js_contains_connect_function():
    js = get_midi_js(1)
    assert "connectMidiDevice" in js


def test_get_midi_js_different_ids():
    """Ensure different bridge IDs produce different JS."""
    js1 = get_midi_js(100)
    js2 = get_midi_js(200)
    assert "const BRIDGE_ID = 100;" in js1
    assert "const BRIDGE_ID = 200;" in js2
    assert "const BRIDGE_ID = 100;" not in js2


def test_get_midi_js_persists_device_selection():
    """Ensure the JS stores and retrieves the MIDI device from localStorage."""
    js = get_midi_js(1)
    assert "localStorage.setItem" in js
    assert "localStorage.getItem" in js
    assert "midi_device_id" in js


def test_get_midi_js_clears_storage_on_disconnect():
    """Ensure disconnecting removes the saved device."""
    js = get_midi_js(1)
    assert "localStorage.removeItem" in js
