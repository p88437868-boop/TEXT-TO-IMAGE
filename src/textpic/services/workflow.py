from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

from textpic.paths import images_dir, new_image_path
from textpic.services.clipboard import ClipboardService
from textpic.services.history_repo import HistoryRepository, MessageRecord
from textpic.services.paste import PasteService
from textpic.services.renderer import RenderConfig, Renderer
from textpic.services.settings_service import SettingsService
from textpic.services.template_repo import TemplateRepository


class Workflow(QObject):
    status_changed = Signal(str)
    error = Signal(str)
    notify = Signal(str, str)
    message_rendered = Signal(int)
    message_pasted = Signal(int)
    data_wiped = Signal()

    def __init__(
        self,
        renderer: Renderer,
        history: HistoryRepository,
        templates: TemplateRepository,
        settings: SettingsService,
        clipboard: ClipboardService,
        paste: PasteService,
    ):
        super().__init__()
        self.renderer = renderer
        self.history = history
        self.templates = templates
        self.settings = settings
        self.clipboard = clipboard
        self.paste = paste
        self.current_id: int | None = None
        self.current_image: QImage | None = None
        self._pending_paste_id: int | None = None
        self.paste.set_delay(self.settings.get_int("paste_delay_ms"))
        self.paste.finished.connect(self._on_paste_finished)

    def render_text(self, text: str, config: RenderConfig) -> MessageRecord:
        result = self.renderer.render(text, config)
        image_path = new_image_path()
        if not result.image.save(str(image_path), "PNG"):
            raise RuntimeError("Could not save the rendered PNG.")
        try:
            record = self.history.add(
                text=text,
                style_key=config.style_key,
                theme=config.theme,
                font=config.font,
                font_size=config.font_size,
                scale=config.scale,
                image_path=str(image_path),
            )
        except Exception:
            self._safe_unlink(image_path)
            raise
        self.current_id = record.id
        self.current_image = result.image
        self.clipboard.set_image(result.image, result.png_bytes)
        paste_hotkey = str(self.settings.get("hotkey_paste") or "F9")
        self.status_changed.emit(f"Rendered ✓ — press {paste_hotkey} in your chat")
        self.message_rendered.emit(record.id)
        return record

    def preview_image(self, text: str, config: RenderConfig) -> QImage:
        return self.renderer.render(text, config).image

    def copy_current(self) -> bool:
        if self.current_image is None:
            render_hotkey = str(self.settings.get("hotkey_render") or "F6")
            self.error.emit(f"Render a message first ({render_hotkey}).")
            return False
        self.clipboard.set_image(self.current_image)
        self.status_changed.emit("Copied ✓")
        return True

    def copy_record(self, record: MessageRecord) -> bool:
        image = self._load_record_image(record)
        if image is None:
            return False
        self.clipboard.set_image(image)
        self.status_changed.emit("Copied ✓")
        return True

    def paste_current(self) -> bool:
        if self.current_image is None:
            self.error.emit("Render a message first so there is an image to paste.")
            return False
        self.clipboard.set_image(self.current_image)
        self._pending_paste_id = self.current_id
        ok, message = self.paste.paste(self.settings.get_int("paste_delay_ms"))
        if not ok:
            self._pending_paste_id = None
            self.error.emit(message)
        return ok

    def paste_record(self, record: MessageRecord) -> bool:
        image = self._load_record_image(record)
        if image is None:
            return False
        self.current_id = record.id
        self.current_image = image
        self.clipboard.set_image(image)
        self._pending_paste_id = record.id
        ok, message = self.paste.paste(self.settings.get_int("paste_delay_ms"))
        if not ok:
            self._pending_paste_id = None
            self.error.emit(message)
        return ok

    def _on_paste_finished(self, success: bool, message: str) -> None:
        if success:
            message_id = self._pending_paste_id
            if message_id is not None:
                self.history.mark_pasted(message_id)
                self.message_pasted.emit(message_id)
            self._pending_paste_id = None
            self.status_changed.emit("Pasted ✓")
            self.notify.emit("success", "Message pasted")
        else:
            self._pending_paste_id = None
            self.error.emit(message)

    def _load_record_image(self, record: MessageRecord) -> QImage | None:
        if not record.image_path:
            self.error.emit("This history entry has no saved image.")
            return None
        path = Path(record.image_path)
        if not path.exists():
            self.error.emit("The PNG for this entry is missing.")
            return None
        image = QImage(str(path))
        if image.isNull():
            self.error.emit("The PNG for this entry could not be opened.")
            return None
        return image

    def pin(self, message_id: int, pinned: bool) -> None:
        self.history.set_pinned(message_id, pinned)

    def delete_messages(self, ids: list[int]) -> int:
        paths = self.history.delete_ids(ids)
        self._delete_images(paths)
        if self.current_id in ids:
            self.current_id = None
            self.current_image = None
        return len(ids)

    def clear_history(self) -> int:
        paths = self.history.clear()
        self._delete_images(paths)
        self.current_id = None
        self.current_image = None
        return len(paths)

    def apply_retention(self) -> None:
        days = self.settings.get_int("retention_days")
        if days <= 0:
            return
        paths = self.history.delete_older_than(days)
        self._delete_images(paths)

    def wipe_data(self) -> None:
        paths = self.history.clear()
        self._delete_images(paths)
        self.templates.seed_defaults(force=True)
        self.settings.reset()
        self.current_id = None
        self.current_image = None
        root = images_dir()
        if root.exists():
            for item in sorted(root.rglob("*"), reverse=True):
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        item.rmdir()
                except OSError:
                    pass
        self.data_wiped.emit()

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass

    def _delete_images(self, paths: list[str]) -> None:
        root = images_dir().resolve()
        for raw in paths:
            try:
                path = Path(raw).resolve()
                if path.is_relative_to(root):
                    path.unlink(missing_ok=True)
            except (OSError, ValueError):
                continue
