from __future__ import annotations

import threading
import time
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

from textpic.native import win32


MODIFIER_NAMES = {
    "ctrl": win32.MOD_CONTROL,
    "control": win32.MOD_CONTROL,
    "alt": win32.MOD_ALT,
    "shift": win32.MOD_SHIFT,
    "win": win32.MOD_WIN,
    "meta": win32.MOD_WIN,
}

KEY_NAMES = {
    "SPACE": 0x20,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "BACKSPACE": 0x08,
    "DELETE": 0x2E,
    "INSERT": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "PRINTSCREEN": 0x2C,
    "PAUSE": 0x13,
}

MODIFIER_ORDER = [
    ("Ctrl", win32.MOD_CONTROL),
    ("Alt", win32.MOD_ALT),
    ("Shift", win32.MOD_SHIFT),
    ("Win", win32.MOD_WIN),
]


def parse_hotkey(sequence: str) -> tuple[int, int]:
    if not sequence or not sequence.strip():
        raise ValueError("Hotkey is empty.")
    parts = [part.strip() for part in sequence.split("+") if part.strip()]
    if not parts:
        raise ValueError("Hotkey is empty.")
    modifiers = 0
    key: str | None = None
    for part in parts:
        lowered = part.lower()
        if lowered in MODIFIER_NAMES:
            modifiers |= MODIFIER_NAMES[lowered]
            continue
        if key is not None:
            raise ValueError("A hotkey can contain only one non-modifier key.")
        key = part
    if key is None:
        raise ValueError("A hotkey needs a regular key, not only modifiers.")

    upper = key.upper()
    if len(upper) == 1 and (upper.isalpha() or upper.isdigit()):
        virtual_key = ord(upper)
    elif upper.startswith("F") and upper[1:].isdigit() and 1 <= int(upper[1:]) <= 24:
        virtual_key = 0x70 + int(upper[1:]) - 1
    elif upper in KEY_NAMES:
        virtual_key = KEY_NAMES[upper]
    else:
        raise ValueError(f"Unsupported hotkey key: {key}")
    return modifiers, virtual_key


def normalize_hotkey(sequence: str) -> str:
    modifiers, virtual_key = parse_hotkey(sequence)
    labels = [name for name, flag in MODIFIER_ORDER if modifiers & flag]
    if 0x70 <= virtual_key <= 0x87:
        key = f"F{virtual_key - 0x70 + 1}"
    elif 0x30 <= virtual_key <= 0x39 or 0x41 <= virtual_key <= 0x5A:
        key = chr(virtual_key)
    else:
        reverse = {
            value: name
            for name, value in KEY_NAMES.items()
            if name not in {"RETURN", "ESCAPE"}
        }
        key = reverse.get(virtual_key, str(virtual_key))
    return "+".join([*labels, key])


class _HotkeyThread(threading.Thread):
    def __init__(self, manager: "HotkeyManager", bindings: dict[str, list[str]]):
        super().__init__(name="TextPicHotkeys", daemon=True)
        self.manager = manager
        self.bindings = {
            action: list(sequences) for action, sequences in bindings.items()
        }
        self.ready = threading.Event()
        self.thread_id: int | None = None

    def run(self) -> None:
        self.thread_id = win32.get_current_thread_id()
        id_to_action: dict[int, str] = {}
        registered: list[int] = []
        index = 1
        for action, sequences in self.bindings.items():
            for sequence in sequences:
                if not sequence:
                    continue
                try:
                    modifiers, virtual_key = parse_hotkey(sequence)
                except ValueError:
                    self.manager.failed.emit(action, sequence)
                    index += 1
                    continue
                if win32.register_hotkey(
                    index,
                    modifiers | win32.MOD_NOREPEAT,
                    virtual_key,
                ):
                    registered.append(index)
                    id_to_action[index] = action
                else:
                    self.manager.failed.emit(action, sequence)
                index += 1
        self.ready.set()
        message = wintypes.MSG()
        try:
            while True:
                result = win32.get_message(message)
                if result in (0, -1):
                    break
                if message.message == win32.WM_HOTKEY:
                    action = id_to_action.get(int(message.wParam))
                    if action:
                        self.manager.triggered.emit(action)
                elif message.message == win32.WM_APP_STOP:
                    break
                else:
                    win32.translate_message(message)
                    win32.dispatch_message(message)
        finally:
            for hotkey_id in registered:
                win32.unregister_hotkey(hotkey_id)

    def stop(self) -> None:
        if not self.ready.wait(1.0):
            return
        if self.thread_id is None:
            return
        win32.post_thread_message(self.thread_id, win32.WM_APP_STOP)
        self.join(1.0)


class HotkeyManager(QObject):
    triggered = Signal(str)
    failed = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: _HotkeyThread | None = None
        self._bindings: dict[str, list[str]] = {}
        self._lock = threading.Lock()

    def set_bindings(self, bindings: dict[str, str | list[str]]) -> None:
        with self._lock:
            self.stop()
            normalized: dict[str, list[str]] = {}
            for action, value in bindings.items():
                sequences = [value] if isinstance(value, str) else list(value)
                cleaned: list[str] = []
                for sequence in sequences:
                    sequence = sequence.strip()
                    if sequence and sequence not in cleaned:
                        cleaned.append(sequence)
                if cleaned:
                    normalized[action] = cleaned
            self._bindings = normalized
            if not self._bindings:
                return
            self._thread = _HotkeyThread(self, self._bindings)
            self._thread.start()

    def stop(self) -> None:
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.stop()

    @property
    def bindings(self) -> dict[str, list[str]]:
        return {
            action: list(sequences) for action, sequences in self._bindings.items()
        }
