from __future__ import annotations

import ctypes
import winsound
from ctypes import wintypes

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from textpic.context import AppContext
from textpic.native import win32
from textpic.paths import assets_path
from textpic.services.hotkeys import HotkeyManager
from textpic.services.template_repo import TemplateRecord
from textpic.services.tray import TrayService
from textpic.theme.icons import ICONS
from textpic.ui.pages.analytics import AnalyticsPage
from textpic.ui.pages.common import initials
from textpic.ui.pages.compose import ComposePage
from textpic.ui.pages.dashboard import DashboardPage
from textpic.ui.pages.help import HelpPage
from textpic.ui.pages.history import HistoryPage
from textpic.ui.pages.settings import SettingsPage
from textpic.ui.pages.templates import (
    TemplatesPage,
    build_template_text,
)
from textpic.ui.widgets.controls import Keycap
from textpic.ui.widgets.toast import ToastManager


PAGE_META = {
    "dashboard": ("Dashboard", "A quiet overview of your message workflow."),
    "compose": ("Compose", "Write it, style it, send it."),
    "history": ("History", "Every rendered message, saved locally."),
    "templates": ("Templates", "Reusable replies with global hotkeys."),
    "analytics": ("Analytics", "See how your messaging rhythm changes."),
    "settings": ("Settings", "Tune hotkeys, startup and local data."),
    "help": ("Help", "Quick answers and keyboard shortcuts."),
}

NAV_ITEMS = [
    ("dashboard", "Dashboard", "dashboard"),
    ("compose", "Compose", "compose"),
    ("history", "History", "history"),
    ("templates", "Templates", "templates"),
    ("analytics", "Analytics", "analytics"),
    ("settings", "Settings", "settings"),
    ("help", "Help", "help"),
]

ACTION_LABELS = {
    "render": "Render & copy",
    "paste": "Paste image",
    "combo": "Open composer",
}


class WindowButton(QPushButton):
    def __init__(
        self,
        icon_name: str,
        tooltip: str,
        close: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._icon_name = icon_name
        self._close = close
        self.setObjectName("WindowCloseButton" if close else "WindowButton")
        self.setIconSize(QSize(14, 14))
        self.setFixedSize(34, 28)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_icon(False)

    def _apply_icon(self, hovered: bool) -> None:
        if self._close and hovered:
            color = "TEXT_ON_ACCENT"
        elif hovered:
            color = "TEXT_PRIMARY"
        else:
            color = "TEXT_SECONDARY"
        self.setIcon(ICONS.icon(self._icon_name, color, 14))

    def set_icon_name(self, icon_name: str) -> None:
        self._icon_name = icon_name
        self._apply_icon(self.underMouse())

    def enterEvent(self, event) -> None:
        self._apply_icon(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._apply_icon(False)
        super().leaveEvent(event)


class TitleBar(QFrame):
    def __init__(self, window: "MainWindow"):
        super().__init__(window)
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)
        self.window_ref = window
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 6, 0)
        layout.setSpacing(2)
        label = QLabel("TEXTPIC STUDIO")
        label.setObjectName("TitleBarLabel")
        layout.addWidget(label)
        layout.addStretch(1)
        self.min_button = window.window_button("minimize", "Minimize")
        self.max_button = window.window_button("maximize", "Maximize")
        self.close_button = window.window_button("close", "Close", close=True)
        self.min_button.clicked.connect(window.showMinimized)
        self.max_button.clicked.connect(window.toggle_maximize)
        self.close_button.clicked.connect(window.close)
        layout.addWidget(self.min_button)
        layout.addWidget(self.max_button)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.window_ref.toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext):
        super().__init__()
        self.context = context
        self._force_quit = False
        self._tray_notice_shown = False
        self._hotkey_failures: set[str] = set()
        self.setWindowTitle("TextPic Studio")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(960, 640)
        self.resize(1400, 900)
        self._build()
        self._size_grip = QSizeGrip(self.root)
        self._size_grip.setFixedSize(16, 16)
        self._size_grip.setToolTip("Resize")
        self._size_grip.move(
            max(0, self.width() - self._size_grip.width() - 2),
            max(0, self.height() - self._size_grip.height() - 2),
        )
        self._size_grip.raise_()
        self._connect_workflow()
        self._connect_tray()
        self._setup_hotkeys()
        self._apply_profile()
        self._update_window_state()
        self.show_page("dashboard")

    def _build(self) -> None:
        root = QFrame()
        root.setObjectName("WindowRoot")
        self.root = root
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        root_layout.addWidget(self.title_bar)

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(0)
        main_row.addWidget(self._build_sidebar())

        right = QWidget()
        right.setObjectName("ContentArea")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._build_topbar())
        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentArea")
        right_layout.addWidget(self.stack, 1)
        main_row.addWidget(right, 1)
        root_layout.addLayout(main_row, 1)

        self.pages = {
            "dashboard": DashboardPage(self.context),
            "compose": ComposePage(self.context),
            "history": HistoryPage(self.context),
            "templates": TemplatesPage(self.context),
            "analytics": AnalyticsPage(self.context),
            "settings": SettingsPage(self.context),
            "help": HelpPage(self.context),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.toasts = ToastManager(self)
        self.tray = TrayService(self)
        self.hotkeys = HotkeyManager(self)
        self._connect_pages()
        self._setup_shortcuts()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(232)
        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        content.setObjectName("SidebarContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(12)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        mark = QLabel()
        mark.setPixmap(
            QIcon(str(assets_path("brand.png"))).pixmap(QSize(34, 34))
        )
        mark.setFixedSize(34, 34)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        name = QLabel("TextPic Studio")
        name.setObjectName("BrandName")
        sub = QLabel("MESSAGE IMAGE STUDIO")
        sub.setObjectName("BrandSub")
        brand_text.addWidget(name)
        brand_text.addWidget(sub)
        brand.addWidget(mark)
        brand.addLayout(brand_text, 1)
        layout.addLayout(brand)

        workspace = QFrame()
        workspace.setObjectName("WorkspaceChip")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(10, 8, 10, 8)
        workspace_layout.setSpacing(1)
        workspace_label = QLabel("WORKSPACE")
        workspace_label.setObjectName("BrandSub")
        self.workspace_name = QLabel("My Workspace")
        self.workspace_name.setObjectName("WorkspaceName")
        workspace_layout.addWidget(workspace_label)
        workspace_layout.addWidget(self.workspace_name)
        layout.addWidget(workspace)

        section = QLabel("MAIN")
        section.setObjectName("BrandSub")
        layout.addWidget(section)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}
        for key, label, icon_name in NAV_ITEMS:
            button = QPushButton(label)
            button.setObjectName("NavItem")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(self._nav_icon(icon_name))
            button.setIconSize(QSize(18, 18))
            button.setMinimumHeight(38)
            button.clicked.connect(
                lambda checked=False, page_key=key: self.show_page(page_key)
            )
            self.nav_group.addButton(button)
            layout.addWidget(button)
            self.nav_buttons[key] = button
        layout.addStretch(1)

        hotkey_card = QFrame()
        hotkey_card.setObjectName("WorkspaceChip")
        hotkey_layout = QVBoxLayout(hotkey_card)
        hotkey_layout.setContentsMargins(10, 9, 10, 9)
        hotkey_layout.setSpacing(6)
        hotkey_header = QHBoxLayout()
        hotkey_label = QLabel("GLOBAL HOTKEYS")
        hotkey_label.setObjectName("BrandSub")
        self.hotkey_state = QLabel("Active")
        self.hotkey_state.setObjectName("StatusText")
        self.hotkey_state.setProperty("tone", "success")
        hotkey_header.addWidget(hotkey_label)
        hotkey_header.addStretch(1)
        hotkey_header.addWidget(self.hotkey_state)
        hotkey_layout.addLayout(hotkey_header)
        self.key_labels: dict[str, Keycap] = {}
        for action, label in (
            ("render", "Render & copy"),
            ("paste", "Paste image"),
            ("combo", "Open composer"),
        ):
            row = QHBoxLayout()
            row.setSpacing(8)
            keycap = Keycap("")
            self.key_labels[action] = keycap
            row.addWidget(keycap)
            action_label = QLabel(label)
            action_label.setObjectName("Hint")
            row.addWidget(action_label, 1)
            hotkey_layout.addLayout(row)
        layout.addWidget(hotkey_card)

        profile = QHBoxLayout()
        profile.setSpacing(9)
        self.avatar = QLabel("TS")
        self.avatar.setObjectName("Avatar")
        self.avatar.setFixedSize(36, 36)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_text = QVBoxLayout()
        profile_text.setSpacing(0)
        self.profile_name = QLabel("You")
        self.profile_name.setObjectName("ProfileName")
        self.profile_role = QLabel("Sales & Support")
        self.profile_role.setObjectName("BrandSub")
        profile_text.addWidget(self.profile_name)
        profile_text.addWidget(self.profile_role)
        settings_button = QPushButton()
        settings_button.setObjectName("NavItem")
        settings_button.setIcon(ICONS.icon("settings", "TEXT_MUTED", 17))
        settings_button.setIconSize(QSize(17, 17))
        settings_button.setFixedSize(34, 34)
        settings_button.setToolTip("Settings")
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.clicked.connect(lambda: self.show_page("settings"))
        profile.addWidget(self.avatar)
        profile.addLayout(profile_text, 1)
        profile.addWidget(settings_button)
        layout.addLayout(profile)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return sidebar

    def _build_topbar(self) -> QFrame:
        topbar = QFrame()
        topbar.setObjectName("TopBar")
        topbar.setFixedHeight(68)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(26, 0, 24, 0)
        layout.setSpacing(14)
        title_column = QVBoxLayout()
        title_column.setSpacing(1)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("TopPageTitle")
        self.page_subtitle = QLabel("")
        self.page_subtitle.setObjectName("PageSubtitle")
        title_column.addWidget(self.page_title)
        title_column.addWidget(self.page_subtitle)
        layout.addLayout(title_column)
        layout.addStretch(1)
        self.top_status = QLabel("Ready")
        self.top_status.setObjectName("StatusText")
        self.top_status.setProperty("tone", "success")
        self.top_status.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.top_status.setMaximumWidth(360)
        layout.addWidget(self.top_status)
        self.keyboard_chip = Keycap("F6")
        layout.addWidget(self.keyboard_chip)
        return topbar

    def _nav_icon(self, icon_name: str) -> QIcon:
        icon = QIcon()
        icon.addPixmap(
            ICONS.pixmap(icon_name, "TEXT_MUTED", 18),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        icon.addPixmap(
            ICONS.pixmap(icon_name, "TEXT_PRIMARY", 18),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            ICONS.pixmap(icon_name, "TEXT_PRIMARY", 18),
            QIcon.Mode.Active,
            QIcon.State.On,
        )
        return icon

    def window_button(
        self, icon_name: str, tooltip: str, close: bool = False
    ) -> WindowButton:
        return WindowButton(icon_name, tooltip, close, self)

    def _connect_pages(self) -> None:
        dashboard = self.pages["dashboard"]
        compose = self.pages["compose"]
        history = self.pages["history"]
        templates = self.pages["templates"]
        analytics = self.pages["analytics"]
        settings = self.pages["settings"]
        help_page = self.pages["help"]
        dashboard.navigate.connect(self.show_page)
        dashboard.use_template.connect(self._use_template)
        dashboard.toast.connect(self.toasts.show)
        compose.toast.connect(self.toasts.show)
        history.navigate.connect(self.show_page)
        history.toast.connect(self.toasts.show)
        templates.compose_requested.connect(self._compose_text)
        templates.templates_changed.connect(self._templates_changed)
        templates.toast.connect(self.toasts.show)
        analytics.toast.connect(self.toasts.show)
        settings.toast.connect(self.toasts.show)
        settings.profile_changed.connect(self._profile_changed)
        settings.settings_saved.connect(self._settings_saved)
        settings.hotkeys_changed.connect(self._bind_hotkeys)
        help_page.navigate.connect(self.show_page)

    def _connect_workflow(self) -> None:
        self.context.workflow.status_changed.connect(self._status_changed)
        self.context.workflow.error.connect(self._workflow_error)
        self.context.workflow.notify.connect(self._workflow_notify)
        self.context.workflow.message_rendered.connect(self._message_rendered)
        self.context.workflow.message_pasted.connect(self._message_pasted)
        self.context.workflow.data_wiped.connect(self._data_wiped)

    def _connect_tray(self) -> None:
        self.tray.show_requested.connect(self.show_window)
        self.tray.render_requested.connect(self._global_render)
        self.tray.paste_requested.connect(self._global_paste)
        self.tray.settings_requested.connect(lambda: self._show_page("settings"))
        self.tray.quit_requested.connect(self.quit_app)

    def _setup_shortcuts(self) -> None:
        for index, key in enumerate(self.pages, start=1):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{index}"), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(
                lambda page_key=key: self.show_page(page_key)
            )

    def _setup_hotkeys(self) -> None:
        self.hotkeys.triggered.connect(self._hotkey_triggered)
        self.hotkeys.failed.connect(self._hotkey_failed)
        self._bind_hotkeys()

    def _bind_hotkeys(self) -> None:
        self._hotkey_failures.clear()
        self._set_hotkey_state("Active", "success")
        bindings: dict[str, list[str]] = {
            "render": [
                str(self.context.settings.get("hotkey_render")),
                str(self.context.settings.get("hotkey_render_alt")),
            ],
            "paste": [
                str(self.context.settings.get("hotkey_paste")),
                str(self.context.settings.get("hotkey_paste_alt")),
            ],
            "combo": [
                str(self.context.settings.get("hotkey_combo")),
                str(self.context.settings.get("hotkey_combo_alt")),
            ],
        }
        for action, sequence in self.context.template_bindings().items():
            bindings[action] = [sequence]
        self.hotkeys.set_bindings(bindings)
        for action, keycap in self.key_labels.items():
            sequences = bindings.get(action, [])
            primary = sequences[0] if sequences else ""
            fallback = sequences[1] if len(sequences) > 1 else ""
            keycap.setText(primary or "—")
            keycap.setToolTip(f"Fallback: {fallback}" if fallback else "")
        self.keyboard_chip.setText(bindings.get("render", [""])[0] or "—")
        self.pages["compose"].update_hotkey_labels()
        self.tray.set_hotkeys(
            bindings.get("render", [""])[0],
            bindings.get("paste", [""])[0],
        )

    def _hotkey_failed(self, action: str, sequence: str) -> None:
        self._hotkey_failures.add(action)
        self._set_hotkey_state("Conflict", "warning")
        label = ACTION_LABELS.get(action, "Quick template")
        self.toasts.warning(
            f"{label}: {sequence} is already in use. Try its fallback shortcut."
        )

    def _set_hotkey_state(self, text: str, tone: str) -> None:
        self.hotkey_state.setText(text)
        self.hotkey_state.setProperty("tone", tone)
        self.hotkey_state.style().unpolish(self.hotkey_state)
        self.hotkey_state.style().polish(self.hotkey_state)

    def _hotkey_triggered(self, action: str) -> None:
        if action == "render":
            self._global_render()
        elif action == "paste":
            self._global_paste()
        elif action == "combo":
            self._global_combo()
        elif action.startswith("template:"):
            try:
                template_id = int(action.split(":", 1)[1])
            except ValueError:
                return
            self._global_template(template_id)

    def _global_render(self) -> None:
        compose = self.pages["compose"]
        if self.isVisible() and self.isActiveWindow():
            if not compose.text().strip():
                self.toasts.info("Type a message first, then press the render hotkey.")
                return
            compose.render_current()
            return
        if self.context.paste.target_blocks_input():
            self._workflow_notify(
                "error",
                "The focused window is elevated. TextPic Studio cannot read its selection.",
            )
            return
        # Browsers can append a trailing newline to copied text, which would
        # otherwise add an empty line and make the image taller than the message.
        text = (self.context.paste.capture_focused_text() or "").strip()
        if not text:
            self._workflow_notify(
                "warning",
                "No text found. Select the text you want to render, then press the hotkey.",
            )
            return
        config = compose.config()
        try:
            self.context.workflow.render_text(text, config)
        except Exception as exc:
            self._workflow_notify("error", str(exc) or "Could not render the selected text.")
            return
        self.context.settings.update(config.to_dict())
        compose.set_text(text, focus=False)

    def _global_paste(self) -> None:
        if self.context.workflow.current_image is None:
            render_hotkey = str(
                self.context.settings.get("hotkey_render") or "F6"
            )
            self._workflow_notify(
                "error", f"Render a message first ({render_hotkey})."
            )
            return
        self.pages["compose"].paste_current()

    def _global_combo(self) -> None:
        if self.context.settings.get_bool("capture_mode"):
            self._capture_finished(self.context.paste.capture_focused_text() or "")
            return
        self._show_page("compose")

    def _capture_finished(self, text: str) -> None:
        self._show_page("compose")
        if text:
            self.pages["compose"].set_text(text)
            self.toasts.success("Selected text captured.")
        else:
            self.toasts.warning("No selected text was captured.")

    def _global_template(self, template_id: int) -> None:
        record = self.context.templates.get(template_id)
        if record is None:
            return
        if not self.isVisible() and not self._template_has_placeholders(record):
            self.pages["compose"].set_text(record.body, focus=False)
            if self.pages["compose"].render_current():
                self.toasts.success(f"“{record.title}” copied.")
            return
        self._show_page("compose")
        self._fill_template(record)

    @staticmethod
    def _template_has_placeholders(record: TemplateRecord) -> bool:
        from textpic.ui.dialogs import placeholder_keys

        return bool(placeholder_keys(record.body))

    def _fill_template(self, record: TemplateRecord) -> None:
        text = build_template_text(record, self)
        if text is not None:
            self.pages["compose"].set_text(text)

    def _use_template(self, template_id: int) -> None:
        record = self.context.templates.get(template_id)
        if record is None:
            return
        self._show_page("compose")
        self._fill_template(record)

    def _compose_text(self, text: str) -> None:
        self._show_page("compose")
        self.pages["compose"].set_text(text)

    def _templates_changed(self) -> None:
        self.pages["templates"].refresh()
        self.pages["dashboard"].refresh()
        self._bind_hotkeys()

    def _profile_changed(self) -> None:
        self._apply_profile()
        self.pages["dashboard"].refresh()

    def _settings_saved(self) -> None:
        self.pages["dashboard"].refresh()

    def _apply_profile(self) -> None:
        display = str(self.context.settings.get("display_name") or "You")
        role = str(self.context.settings.get("role") or "")
        workspace = str(
            self.context.settings.get("workspace_name") or "My Workspace"
        )
        self.profile_name.setText(display)
        self.profile_role.setText(role or "Local workspace")
        self.workspace_name.setText(workspace)
        self.avatar.setText(initials(display))

    def _is_window_shown(self) -> bool:
        return (
            self.isVisible()
            and not self.isMinimized()
            and self.isActiveWindow()
        )

    def _status_changed(self, text: str) -> None:
        self.top_status.setText(text)
        self.top_status.setProperty("tone", "success")
        self._repolish(self.top_status)
        if not self._is_window_shown() and self.tray.available:
            self.tray.show_message("TextPic Studio", text)

    def _workflow_error(self, message: str) -> None:
        self.top_status.setText("Action needs attention")
        self.top_status.setProperty("tone", "danger")
        self._repolish(self.top_status)
        if self._is_window_shown():
            self.toasts.error(message)
        elif self.tray.available:
            self.tray.show_message("TextPic Studio", message)

    def _workflow_notify(self, kind: str, message: str) -> None:
        if self._is_window_shown():
            self.toasts.show(kind, message)
        elif self.tray.available:
            self.tray.show_message("TextPic Studio", message)

    def _message_rendered(self, _message_id: int) -> None:
        self._refresh_data()
        self._play_sound()

    def _message_pasted(self, _message_id: int) -> None:
        self.pages["compose"].clear_after_paste()
        self._refresh_data()
        self._play_sound()

    def _refresh_data(self) -> None:
        self.pages["dashboard"].refresh()
        self.pages["history"].refresh()
        self.pages["analytics"].refresh()

    def _data_wiped(self) -> None:
        for page in self.pages.values():
            refresh = getattr(page, "refresh", None)
            if callable(refresh):
                refresh()
        self.pages["compose"].clear_text()
        self.pages["settings"].load_from_settings()
        self._apply_profile()
        self._bind_hotkeys()
        self.show_page("dashboard")

    def _play_sound(self) -> None:
        if not self.context.settings.get_bool("sound"):
            return
        path = assets_path("sounds", "click.wav")
        if path.exists():
            try:
                winsound.PlaySound(
                    str(path), winsound.SND_FILENAME | winsound.SND_ASYNC
                )
            except RuntimeError:
                pass

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def show_page(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        button = self.nav_buttons.get(key)
        if button is not None:
            button.setChecked(True)
        title, subtitle = PAGE_META.get(key, ("TextPic Studio", ""))
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        if key == "dashboard":
            page.refresh()
        elif key == "analytics":
            page.refresh()
        elif key == "templates":
            page.refresh()
        elif key == "history":
            page.refresh()

    def _show_page(self, key: str) -> None:
        self.show_window()
        self.show_page(key)

    def show_window(self) -> None:
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()
        handle = self.windowHandle()
        if handle is not None:
            handle.requestActivate()

    def toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._update_window_state()

    def _update_window_state(self) -> None:
        maximized = self.isMaximized()
        self.root.setProperty("maximized", "true" if maximized else "false")
        self._repolish(self.root)
        icon = "restore" if maximized else "maximize"
        self.title_bar.max_button.set_icon_name(icon)
        self.title_bar.max_button.setToolTip(
            "Restore" if maximized else "Maximize"
        )
        grip = getattr(self, "_size_grip", None)
        if grip is not None:
            grip.setVisible(not maximized)

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_window_state()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        grip = getattr(self, "_size_grip", None)
        if grip is not None:
            grip.move(self.width() - grip.width() - 2, self.height() - grip.height() - 2)
            grip.raise_()

    def nativeEvent(self, event_type, message):
        event_name = (
            bytes(event_type)
            if hasattr(event_type, "data")
            else str(event_type).encode("utf-8", errors="ignore")
        )
        if event_name in (b"windows_generic_MSG", b'"windows_generic_MSG"'):
            try:
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == win32.WM_NCHITTEST:
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    hit = win32.resize_hit_test(int(self.winId()), x, y, 8)
                    if hit:
                        return True, hit
            except (ValueError, OSError):
                pass
        return super().nativeEvent(event_type, message)

    def closeEvent(self, event) -> None:
        if (
            not self._force_quit
            and self.context.settings.get_bool("close_to_tray")
            and self.tray.available
        ):
            self.hide()
            event.ignore()
            if not self._tray_notice_shown:
                self._tray_notice_shown = True
                render = str(self.context.settings.get("hotkey_render") or "F6")
                paste = str(self.context.settings.get("hotkey_paste") or "F9")
                self.tray.show_message(
                    "TextPic Studio is still running",
                    f"Use the tray icon, or press {render} and {paste} from any app.",
                )
            return
        self._force_quit = True
        self.hotkeys.stop()
        self.tray.hide()
        event.accept()
        QApplication.instance().quit()

    def quit_app(self) -> None:
        self._force_quit = True
        self.hotkeys.stop()
        self.tray.hide()
        QApplication.instance().quit()

    def shutdown(self) -> None:
        self.hotkeys.stop()
        self.tray.hide()

    def show_startup(self) -> None:
        if self.context.settings.get_bool("start_minimized") and self.tray.available:
            self.hide()
        else:
            self.show_window()
