"""MIDI bridge — connects browser Web MIDI API to Python handlers via NiceGUI events."""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from datetime import datetime

from nicegui import ui

from app.midi.midi_js import get_midi_js

log = logging.getLogger(__name__)

MAX_LOG_ENTRIES = 200


@dataclass
class MidiEvent:
    timestamp: str
    message: str
    event_type: (
        str  # 'note_on', 'note_off', 'status', 'devices', 'info', 'error'
    )


class MidiBridge:
    """Per-client MIDI bridge.

    Creates a hidden DOM element that acts as a JS→Python event bridge.
    JavaScript dispatches CustomEvents on this element; NiceGUI .on() handlers
    forward them to Python callbacks.
    """

    def __init__(self) -> None:
        self.connected: bool = False
        self.device_name: str = ""
        self.devices: list[dict] = []
        self.log_entries: list[MidiEvent] = []
        self.on_note_callback = (
            None  # callable(note, velocity) set by drill/games
        )

        # UI references (set during setup)
        self._badge: ui.badge | None = None
        self._device_select: ui.select | None = None
        self._log_container: ui.column | None = None

        # Hidden bridge element for JS→Python events
        self._bridge = ui.element("div").style("display:none")
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers on the bridge element."""
        self._bridge.on(
            "midi-note-on",
            lambda e: self._on_note_on(e.args),
            js_handler="(e) => emit(e.detail)",
        )
        self._bridge.on(
            "midi-note-off",
            lambda e: self._on_note_off(e.args),
            js_handler="(e) => emit(e.detail)",
        )
        self._bridge.on(
            "midi-devices",
            lambda e: self._on_devices(e.args),
            js_handler="(e) => emit(e.detail)",
        )
        self._bridge.on(
            "midi-status",
            lambda e: self._on_status(e.args),
            js_handler="(e) => emit(e.detail)",
        )

    def inject_js(self) -> None:
        """Inject the Web MIDI API JavaScript into the browser."""
        js_code = get_midi_js(self._bridge.id)
        ui.run_javascript(js_code)

    def bind_ui(
        self,
        badge: ui.badge,
        device_select: ui.select,
        log_container: ui.column,
    ) -> None:
        """Bind UI elements for live updates."""
        self._badge = badge
        self._device_select = device_select
        self._log_container = log_container

        # When user selects a device, connect to it
        device_select.on_value_change(self._on_device_selected)

    def _on_device_selected(self, e) -> None:
        device_id = e.value
        if device_id:
            ui.run_javascript(f"connectMidiDevice({device_id!r})")
        else:
            ui.run_javascript("connectMidiDevice(null)")

    # --- Event handlers ---

    async def _on_note_on(self, data: dict) -> None:
        note = data.get("note", 0)
        velocity = data.get("velocity", 0)
        name = data.get("name", "?")
        self._add_log(
            f"NOTE ON:  {name} (MIDI {note}) vel={velocity}", "note_on"
        )
        if self.on_note_callback and velocity > 0:
            result = self.on_note_callback(note, velocity)
            if inspect.isawaitable(result):
                await result

    def _on_note_off(self, data: dict) -> None:
        note = data.get("note", 0)
        name = data.get("name", "?")
        self._add_log(f"NOTE OFF: {name} (MIDI {note})", "note_off")

    def _on_devices(self, data: dict) -> None:
        self.devices = data.get("devices", [])
        options = {d["id"]: d["name"] for d in self.devices}
        if self._device_select:
            self._device_select.options = options
            self._device_select.update()
        if self.devices:
            self._add_log(
                f"Devices found: {', '.join(d['name'] for d in self.devices)}",
                "info",
            )
        else:
            self._add_log("No MIDI devices detected.", "info")

    def _on_status(self, data: dict) -> None:
        self.connected = data.get("connected", False)
        self.device_name = data.get("device", "")
        device_id = data.get("device_id", "")
        error = data.get("error", "")

        if error:
            self._add_log(error, "error")

        if self._badge:
            if error:
                self._badge.text = f"MIDI: {error}"
                self._badge._props["color"] = "red"
            elif self.connected:
                self._badge.text = f"MIDI: {self.device_name}"
                self._badge._props["color"] = "green"
            else:
                self._badge.text = "MIDI: Disconnected"
                self._badge._props["color"] = "grey"
            self._badge.update()

        # Sync dropdown value on auto-reconnect
        if self._device_select and self.connected and device_id:
            self._device_select.value = device_id

    # --- Logging ---

    def _add_log(self, message: str, event_type: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = MidiEvent(timestamp=ts, message=message, event_type=event_type)
        self.log_entries.append(entry)
        if len(self.log_entries) > MAX_LOG_ENTRIES:
            self.log_entries = self.log_entries[-MAX_LOG_ENTRIES:]

        if self._log_container:
            self._render_log_entry(entry)

    def _render_log_entry(self, entry: MidiEvent) -> None:
        color_map = {
            "note_on": "text-green-400",
            "note_off": "text-grey-500",
            "info": "text-blue-400",
            "error": "text-red-400",
        }
        css_class = color_map.get(entry.event_type, "text-grey-300")
        with self._log_container:
            ui.label(f"[{entry.timestamp}] {entry.message}").classes(
                f"font-mono text-xs {css_class} leading-tight"
            )
        # Auto-scroll to bottom
        ui.run_javascript(
            f'document.getElementById("midi-log-scroll").scrollTop = '
            f'document.getElementById("midi-log-scroll").scrollHeight'
        )
