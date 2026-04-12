"""Web MIDI API JavaScript — injected into the browser for zero-latency MIDI input."""

MIDI_JS = """
(function() {
    'use strict';

    const BRIDGE_ID = {bridge_id};

    // State
    let midiAccess = null;
    let activeInput = null;

    // Note name lookup
    const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    function midiToName(midi) {
        return NOTE_NAMES[midi % 12] + (Math.floor(midi / 12) - 1);
    }

    // Fire a custom DOM event on the bridge element so NiceGUI .on() picks it up
    function fireBridge(eventName, detail) {
        const el = getHtmlElement(BRIDGE_ID);
        if (!el) return;
        el.dispatchEvent(new CustomEvent(eventName, { bubbles: true, detail: detail }));
    }

    // --- Keyboard highlight helpers ---
    function highlightKey(note) {
        const el = document.getElementById('piano-key-' + note);
        if (el) el.setAttribute('fill', el.dataset.activeColor);
    }
    function unhighlightKey(note) {
        const el = document.getElementById('piano-key-' + note);
        if (el) el.setAttribute('fill', el.dataset.defaultColor);
    }

    // --- MIDI message handler ---
    function onMIDIMessage(event) {
        const [status, note, velocity] = event.data;
        const command = status & 0xF0;

        if (command === 0x90 && velocity > 0) {
            highlightKey(note);
            fireBridge('midi-note-on', { note: note, velocity: velocity, name: midiToName(note) });
        } else if (command === 0x80 || (command === 0x90 && velocity === 0)) {
            unhighlightKey(note);
            fireBridge('midi-note-off', { note: note, name: midiToName(note) });
        }
    }

    // --- Connect to a device by ID ---
    window.connectMidiDevice = function(deviceId) {
        if (activeInput) {
            activeInput.onmidimessage = null;
            activeInput = null;
        }
        if (!deviceId || !midiAccess) {
            fireBridge('midi-status', { connected: false, device: '' });
            return;
        }
        const input = midiAccess.inputs.get(deviceId);
        if (!input) {
            fireBridge('midi-status', { connected: false, device: '', error: 'Device not found' });
            return;
        }
        activeInput = input;
        input.onmidimessage = onMIDIMessage;
        fireBridge('midi-status', { connected: true, device: input.name });
    };

    // --- Refresh device list ---
    function refreshDevices() {
        const devices = [];
        for (const input of midiAccess.inputs.values()) {
            devices.push({ id: input.id, name: input.name, state: input.state });
        }
        fireBridge('midi-devices', { devices: devices });

        // If active input got disconnected
        if (activeInput) {
            const still = midiAccess.inputs.get(activeInput.id);
            if (!still || still.state !== 'connected') {
                activeInput = null;
                fireBridge('midi-status', { connected: false, device: '' });
            }
        }
    }

    // --- Init ---
    async function init() {
        if (!navigator.requestMIDIAccess) {
            fireBridge('midi-status', { connected: false, device: '', error: 'Web MIDI API not supported. Use Chrome or Edge.' });
            return;
        }
        try {
            midiAccess = await navigator.requestMIDIAccess({ sysex: false });
            midiAccess.onstatechange = () => refreshDevices();
            refreshDevices();
        } catch (err) {
            fireBridge('midi-status', { connected: false, device: '', error: 'MIDI access denied: ' + err.message });
        }
    }

    init();
})();
"""


def get_midi_js(bridge_id: int) -> str:
    """Return the Web MIDI JavaScript code with the bridge element ID injected."""
    return MIDI_JS.replace("{bridge_id}", str(bridge_id))
