from __future__ import annotations

import logging
import threading
import time

from PySide6.QtCore import QObject, Signal

from textpic.native import win32

LOGGER = logging.getLogger("textpic")


class PasteService(QObject):
    finished = Signal(bool, str)

    def __init__(self, delay_ms: int = 80):
        super().__init__()
        self.delay_ms = delay_ms
        self._lock = threading.Lock()
        self._busy = False

    def set_delay(self, delay_ms: int) -> None:
        self.delay_ms = max(0, min(2000, int(delay_ms)))

    def target_blocks_input(self) -> bool:
        return win32.target_blocks_input()

    def paste(self, delay_ms: int | None = None) -> tuple[bool, str]:
        if self.target_blocks_input():
            return (
                False,
                "The focused window is elevated. Press Ctrl+V there manually, "
                "or run TextPic Studio as administrator.",
            )
        with self._lock:
            if self._busy:
                return False, "A paste is already in progress."
            self._busy = True
        delay = self.delay_ms if delay_ms is None else max(0, int(delay_ms))
        thread = threading.Thread(
            target=self._worker,
            args=(delay,),
            name="TextPicPaste",
            daemon=True,
        )
        thread.start()
        return True, ""

    def _worker(self, delay_ms: int) -> None:
        try:
            deadline = time.monotonic() + 1.0
            while win32.modifier_keys_down() and time.monotonic() < deadline:
                time.sleep(0.01)
            if delay_ms:
                time.sleep(delay_ms / 1000.0)
            if self.target_blocks_input():
                self.finished.emit(
                    False,
                    "The focused window is elevated. Press Ctrl+V there manually.",
                )
                return
            if win32.send_key_combination(win32.VK_V):
                self.finished.emit(True, "")
            else:
                self.finished.emit(
                    False, "Windows blocked the synthetic key press (SendInput)."
                )
        except Exception as exc:  # defensive: this runs on a background thread
            self.finished.emit(False, f"Paste failed: {exc}")
        finally:
            with self._lock:
                self._busy = False

    def capture_focused_text(self) -> str | None:
        """Reads the selection, falling back to the whole focused field."""
        if self.target_blocks_input():
            LOGGER.info("Capture skipped: foreground window is elevated.")
            return None
        deadline = time.monotonic() + 1.0
        while win32.modifier_keys_down() and time.monotonic() < deadline:
            time.sleep(0.01)
        target = win32.foreground_info()
        LOGGER.info(
            "Capturing text from foreground window: %r",
            target.title if target is not None else None,
        )
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        backup = self._snapshot_clipboard(clipboard)
        cleared = win32.clear_clipboard()
        baseline = None if cleared else win32.clipboard_sequence()
        time.sleep(0.03)
        if not win32.send_key_combination(win32.VK_C):
            LOGGER.info("Capture failed: SendInput was blocked for Ctrl+C.")
            return None
        captured = self._wait_for_text(0.5, baseline)
        if captured:
            LOGGER.info("Captured selected text (%d chars).", len(captured))
            return captured
        if not win32.send_key_combination(win32.VK_A):
            self._restore_clipboard(clipboard, backup)
            return None
        # React editors (Facebook, Teams, Discord) need a moment to select.
        time.sleep(0.2)
        baseline = None if cleared else win32.clipboard_sequence()
        if not win32.send_key_combination(win32.VK_C):
            self._restore_clipboard(clipboard, backup)
            return None
        captured = self._wait_for_text(1.0, baseline)
        if captured:
            LOGGER.info("Captured whole focused field (%d chars).", len(captured))
        else:
            LOGGER.info("Clipboard stayed empty after Ctrl+A/Ctrl+C.")
            self._restore_clipboard(clipboard, backup)
        return captured

    @staticmethod
    def _wait_for_text(timeout: float, baseline: int | None) -> str:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            time.sleep(0.04)
            if baseline is not None and win32.clipboard_sequence() == baseline:
                continue
            captured = win32.get_clipboard_text()
            if captured:
                return captured
        return ""

    @staticmethod
    def _snapshot_clipboard(clipboard) -> dict[str, object] | None:
        mime = clipboard.mimeData()
        if mime is None:
            return None
        return {item: mime.data(item) for item in mime.formats()}

    @staticmethod
    def _restore_clipboard(clipboard, snapshot: dict[str, object] | None) -> None:
        if not snapshot:
            return
        from PySide6.QtCore import QMimeData

        mime = QMimeData()
        for item, data in snapshot.items():
            mime.setData(item, data)
        clipboard.setMimeData(mime)
