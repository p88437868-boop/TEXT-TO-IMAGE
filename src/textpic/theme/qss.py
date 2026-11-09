from __future__ import annotations

from pathlib import Path

from textpic.theme import tokens


def build_stylesheet(assets_dir: Path) -> str:
    c = tokens.COLORS
    radius = tokens.RADIUS
    font = tokens.TYPOGRAPHY["ui"]
    assets = Path(assets_dir).as_posix()
    check = f"{assets}/ui/check_on.svg"
    chevron_down = f"{assets}/ui/chevron_down.svg"
    chevron_up = f"{assets}/ui/chevron_up.svg"

    qss = f"""
    QWidget {{
        color: {c['TEXT_SECONDARY']};
        font-family: {font};
        font-size: 13px;
        background: transparent;
    }}
    QMainWindow, QDialog {{
        background: {c['BG_CANVAS']};
    }}
    QFrame#WindowRoot {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {c['BG_GLOW_START']},
            stop:0.42 {c['BG_CANVAS']},
            stop:1 {c['BG_GLOW_END']});
        border: 1px solid {c['BORDER_SUBTLE']};
        border-radius: {radius['window']}px;
    }}
    QFrame#TitleBar {{
        background: transparent;
        border: none;
    }}
    QFrame#Sidebar {{
        background: {c['SURFACE_SIDEBAR']};
        border: none;
        border-right: 1px solid {c['BORDER_SUBTLE']};
        border-bottom-left-radius: {radius['window']}px;
    }}
    QFrame#TopBar {{
        background: transparent;
        border: none;
        border-bottom: 1px solid {c['BORDER_SUBTLE']};
    }}
    QWidget#ContentArea, QWidget#Page, QScrollArea, QScrollArea > QWidget > QWidget {{
        background: transparent;
        border: none;
    }}
    QLabel {{
        background: transparent;
        color: {c['TEXT_SECONDARY']};
    }}
    QLabel#BrandName {{
        color: {c['TEXT_PRIMARY']};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#BrandSub {{
        color: {c['TEXT_MUTED']};
        font-size: 10px;
    }}
    QLabel#PageTitle {{
        color: {c['TEXT_PRIMARY']};
        font-size: {tokens.TYPOGRAPHY['display']}px;
        font-weight: 600;
    }}
    QLabel#PageSubtitle {{
        color: {c['TEXT_MUTED']};
        font-size: 12px;
    }}
    QLabel#SectionTitle {{
        color: {c['TEXT_PRIMARY']};
        font-size: {tokens.TYPOGRAPHY['h2']}px;
        font-weight: 600;
    }}
    QLabel#CardTitle {{
        color: {c['TEXT_PRIMARY']};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#CardSubtitle {{
        color: {c['TEXT_MUTED']};
        font-size: 11px;
    }}
    QLabel#MetricLabel {{
        color: {c['TEXT_MUTED']};
        font-size: 12px;
    }}
    QLabel#MetricValue {{
        color: {c['TEXT_PRIMARY']};
        font-size: {tokens.TYPOGRAPHY['metric']}px;
        font-weight: 700;
    }}
    QLabel#MetricDetail {{
        color: {c['TEXT_MUTED']};
        font-size: 11px;
    }}
    QLabel#MetricIcon {{
        background: {c['ACCENT_SOFT']};
        border-radius: 8px;
        padding: 3px;
    }}
    QLabel#ChartValue {{
        color: {c['TEXT_PRIMARY']};
        font-size: 20px;
        font-weight: 600;
    }}
    QLabel#Muted {{
        color: {c['TEXT_MUTED']};
    }}
    QLabel#Hint {{
        color: {c['TEXT_MUTED']};
        font-size: 11px;
    }}
    QLabel#EmptyTitle {{
        color: {c['TEXT_PRIMARY']};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#EmptyBody {{
        color: {c['TEXT_MUTED']};
        font-size: 12px;
    }}
    QLabel#FormLabel {{
        color: {c['TEXT_SECONDARY']};
        font-size: 12px;
    }}
    QLabel#StatusText {{
        color: {c['TEXT_SECONDARY']};
        font-size: 12px;
    }}
    QLabel#StatusText[tone="success"] {{ color: {c['SUCCESS']}; }}
    QLabel#StatusText[tone="danger"] {{ color: {c['DANGER']}; }}
    QLabel#StatusText[tone="warning"] {{ color: {c['WARNING']}; }}
    QLabel#StatusText[tone="accent"] {{ color: {c['ACCENT']}; }}
    QLabel#ChartLegend {{
        color: {c['TEXT_MUTED']};
        font-size: 11px;
    }}
    QLabel#Avatar {{
        background: {c['ACCENT_SOFT']};
        color: {c['TEXT_PRIMARY']};
        border: 1px solid {c['BORDER_STRONG']};
        border-radius: 18px;
        font-size: 12px;
        font-weight: 600;
        qproperty-alignment: AlignCenter;
    }}
    QLabel#Chip {{
        background: {c['ACCENT_SOFT']};
        color: {c['ACCENT']};
        border-radius: {radius['chip']}px;
        padding: 4px 9px;
        font-size: 11px;
        font-weight: 600;
    }}
    QLabel#Chip[tone="success"] {{
        background: {c['SUCCESS_SOFT']};
        color: {c['SUCCESS']};
    }}
    QLabel#Chip[tone="danger"] {{
        background: {c['DANGER_SOFT']};
        color: {c['DANGER']};
    }}
    QLabel#Chip[tone="warning"] {{
        background: {c['WARNING_SOFT']};
        color: {c['WARNING']};
    }}
    QLabel#Chip[tone="muted"] {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_MUTED']};
    }}
    QLabel#Chip[tone="info"] {{
        background: {c['INFO_SOFT']};
        color: {c['INFO']};
    }}
    QLabel#Keycap {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_SECONDARY']};
        border: 1px solid {c['BORDER_STRONG']};
        border-radius: 6px;
        padding: 2px 6px;
        font-size: 10px;
        font-weight: 600;
    }}
    QFrame#Card {{
        background: {c['SURFACE_CARD']};
        border: 1px solid {c['BORDER_SUBTLE']};
        border-radius: {radius['card']}px;
    }}
    QFrame#Card:hover {{
        background: {c['SURFACE_CARD']};
    }}
    QFrame#MetricCard {{
        background: {c['SURFACE_CARD']};
        border: 1px solid {c['BORDER_SUBTLE']};
        border-radius: {radius['card']}px;
    }}
    QFrame#TemplateCard {{
        background: {c['SURFACE_CARD']};
        border: 1px solid {c['BORDER_SUBTLE']};
        border-radius: {radius['card']}px;
    }}
    QFrame#TemplateCard:hover {{
        background: {c['SURFACE_CARD_HOVER']};
        border-color: {c['BORDER_STRONG']};
    }}
    QFrame#WorkspaceChip {{
        background: {c['SURFACE_INPUT']};
        border: 1px solid {c['BORDER_SUBTLE']};
        border-radius: 9px;
    }}
    QFrame#Divider, QFrame#VLine {{
        background: {c['BORDER_SUBTLE']};
        border: none;
    }}
    QFrame#OptionBar {{
        background: {c['SURFACE_INPUT']};
        border: 1px solid {c['BORDER_SUBTLE']};
        border-radius: {radius['input']}px;
    }}
    QPushButton {{
        background: transparent;
        color: {c['TEXT_SECONDARY']};
        border: 1px solid transparent;
        border-radius: {radius['button']}px;
        padding: 7px 12px;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background: {c['SURFACE_CARD_HOVER']};
        color: {c['TEXT_PRIMARY']};
    }}
    QPushButton:pressed {{
        background: {c['SURFACE_SELECTED']};
    }}
    QPushButton:focus {{
        border: 1px solid {c['BORDER_FOCUS']};
    }}
    QPushButton:disabled {{
        color: {c['TEXT_DISABLED']};
        background: transparent;
        border-color: transparent;
    }}
    QPushButton[role="primary"] {{
        background: {c['ACCENT']};
        color: {c['TEXT_ON_ACCENT']};
        border: 1px solid {c['ACCENT']};
        font-weight: 600;
        padding: 9px 16px;
        min-height: 20px;
    }}
    QPushButton[role="primary"]:hover {{
        background: {c['ACCENT_HOVER']};
        border-color: {c['ACCENT_HOVER']};
        color: {c['TEXT_ON_ACCENT']};
    }}
    QPushButton[role="primary"]:pressed {{
        background: {c['ACCENT_PRESSED']};
        border-color: {c['ACCENT_PRESSED']};
    }}
    QPushButton[role="primary"]:focus {{
        border: 1px solid {c['TEXT_PRIMARY']};
    }}
    QPushButton[role="primary"]:disabled {{
        background: {c['ACCENT_SOFT']};
        border-color: transparent;
        color: {c['TEXT_DISABLED']};
    }}
    QPushButton[role="ghost"] {{
        background: {c['SURFACE_INPUT']};
        border: 1px solid {c['BORDER_SUBTLE']};
        color: {c['TEXT_SECONDARY']};
        padding: 8px 14px;
    }}
    QPushButton[role="ghost"]:hover {{
        background: {c['SURFACE_CARD_HOVER']};
        border-color: {c['BORDER_STRONG']};
        color: {c['TEXT_PRIMARY']};
    }}
    QPushButton[role="ghost"]:focus {{
        border: 1px solid {c['BORDER_FOCUS']};
    }}
    QPushButton[role="ghost"]:disabled {{
        background: {c['SURFACE_INPUT']};
        border-color: {c['BORDER_SUBTLE']};
        color: {c['TEXT_DISABLED']};
    }}
    QPushButton[role="danger"] {{
        background: transparent;
        border: 1px solid {c['BORDER_SUBTLE']};
        color: {c['DANGER']};
    }}
    QPushButton[role="danger"]:hover {{
        background: {c['DANGER_SOFT']};
        border-color: {c['DANGER']};
    }}
    QPushButton[role="danger"]:disabled {{
        background: transparent;
        border-color: {c['BORDER_SUBTLE']};
        color: {c['TEXT_DISABLED']};
    }}
    QPushButton[role="link"] {{
        border: none;
        background: transparent;
        color: {c['ACCENT']};
        padding: 2px 0;
        font-weight: 600;
        text-align: left;
    }}
    QPushButton[role="link"]:hover {{
        color: {c['ACCENT_HOVER']};
        background: transparent;
    }}
    QPushButton[role="link"]:disabled {{
        color: {c['TEXT_DISABLED']};
        background: transparent;
        border: none;
    }}
    QPushButton[size="sm"] {{
        padding: 4px 9px;
        font-size: 11px;
        min-height: 18px;
    }}
    QPushButton[role="icon"] {{
        background: transparent;
        border: none;
        border-radius: 9px;
        padding: 5px;
        min-width: 30px;
        min-height: 30px;
    }}
    QPushButton[role="icon"]:hover {{
        background: {c['SURFACE_CARD_HOVER']};
    }}
    QPushButton[role="segment"] {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 7px;
        padding: 5px 10px;
        font-size: 11px;
        color: {c['TEXT_MUTED']};
    }}
    QPushButton[role="segment"]:checked {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_PRIMARY']};
        border-color: {c['BORDER_STRONG']};
    }}
    QPushButton[role="segment"]:hover {{
        color: {c['TEXT_PRIMARY']};
    }}
    QPushButton#NavItem {{
        background: transparent;
        border: none;
        border-radius: {radius['nav']}px;
        color: {c['TEXT_SECONDARY']};
        padding: 9px 12px;
        text-align: left;
        font-size: 12px;
    }}
    QPushButton#NavItem:hover {{
        background: {c['SURFACE_CARD_HOVER']};
        color: {c['TEXT_PRIMARY']};
    }}
    QPushButton#NavItem:checked {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_PRIMARY']};
        font-weight: 600;
    }}
    QPushButton#NavItem:focus {{
        border: 1px solid {c['BORDER_FOCUS']};
    }}
    QPushButton#WindowButton {{
        background: transparent;
        border: none;
        border-radius: 6px;
        min-width: 34px;
        max-width: 34px;
        min-height: 28px;
        max-height: 28px;
        padding: 0;
    }}
    QPushButton#WindowButton:hover {{
        background: {c['SURFACE_CARD_HOVER']};
    }}
    QPushButton#WindowCloseButton {{
        background: transparent;
        border: none;
        border-radius: 6px;
        min-width: 34px;
        max-width: 34px;
        min-height: 28px;
        max-height: 28px;
        padding: 0;
    }}
    QPushButton#WindowCloseButton:hover {{
        background: {c['DANGER']};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDateEdit {{
        background: {c['SURFACE_INPUT']};
        color: {c['TEXT_PRIMARY']};
        border: 1px solid {c['BORDER_SUBTLE']};
        border-radius: {radius['input']}px;
        padding: 7px 10px;
        selection-background-color: {c['ACCENT']};
        selection-color: {c['TEXT_ON_ACCENT']};
    }}
    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QComboBox:hover,
    QSpinBox:hover, QDateEdit:hover {{
        border-color: {c['BORDER_STRONG']};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
    QSpinBox:focus, QDateEdit:focus {{
        border: 1px solid {c['BORDER_FOCUS']};
    }}
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled,
    QComboBox:disabled, QSpinBox:disabled, QDateEdit:disabled {{
        color: {c['TEXT_DISABLED']};
        border-color: {c['BORDER_SUBTLE']};
        background: {c['SURFACE_INPUT']};
    }}
    QLineEdit#SearchField {{
        padding-left: 10px;
        padding-right: 10px;
        min-height: 22px;
        font-size: 12px;
    }}
    QTextEdit#MessageEditor {{
        font-family: "Segoe UI", "Segoe UI Variable", sans-serif;
        font-size: 15px;
        padding: 12px;
        border-radius: 12px;
    }}
    QLineEdit#HotkeyBox {{
        font-family: "Consolas", "Cascadia Mono", monospace;
        font-size: 12px;
        font-weight: 600;
        color: {c['TEXT_PRIMARY']};
    }}
    QComboBox {{
        padding-right: 26px;
        min-height: 20px;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 22px;
        border: none;
        background: transparent;
    }}
    QComboBox::down-arrow {{
        image: url("{chevron_down}");
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background: {c['SURFACE_CARD']};
        color: {c['TEXT_SECONDARY']};
        border: 1px solid {c['BORDER_STRONG']};
        border-radius: 8px;
        outline: none;
        selection-background-color: {c['SURFACE_SELECTED']};
        selection-color: {c['TEXT_PRIMARY']};
        padding: 4px;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 6px 8px;
        border-radius: 6px;
        min-height: 20px;
    }}
    QComboBox QAbstractItemView::item:selected {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_PRIMARY']};
    }}
    QSpinBox, QDateEdit {{
        padding-right: 24px;
    }}
    QSpinBox::up-button, QDateEdit::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 18px;
        border: none;
        background: transparent;
    }}
    QSpinBox::down-button, QDateEdit::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 18px;
        border: none;
        background: transparent;
    }}
    QSpinBox::up-arrow {{
        image: url("{chevron_up}");
        width: 8px;
        height: 8px;
    }}
    QSpinBox::down-arrow {{
        image: url("{chevron_down}");
        width: 8px;
        height: 8px;
    }}
    QDateEdit::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 22px;
        border: none;
        background: transparent;
    }}
    QDateEdit::down-arrow {{
        image: url("{chevron_down}");
        width: 10px;
        height: 10px;
    }}
    QCheckBox {{
        color: {c['TEXT_SECONDARY']};
        spacing: 8px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 5px;
        border: 1px solid {c['BORDER_STRONG']};
        background: {c['SURFACE_INPUT']};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c['ACCENT']};
    }}
    QCheckBox::indicator:checked {{
        background: {c['ACCENT']};
        border-color: {c['ACCENT']};
        image: url("{check}");
    }}
    QCheckBox::indicator:focus {{
        border: 1px solid {c['BORDER_FOCUS']};
    }}
    QTableView {{
        background: transparent;
        alternate-background-color: transparent;
        border: none;
        gridline-color: transparent;
        outline: none;
        selection-background-color: transparent;
        selection-color: {c['TEXT_PRIMARY']};
    }}
    QTableView::item {{
        border: none;
        border-bottom: 1px solid {c['BORDER_SUBTLE']};
        padding: 4px 8px;
        color: {c['TEXT_SECONDARY']};
    }}
    QTableView::item:hover {{
        background: {c['SURFACE_CARD_HOVER']};
    }}
    QTableView::item:selected {{
        background: {c['ACCENT_SOFT']};
        color: {c['TEXT_PRIMARY']};
    }}
    QHeaderView {{
        background: transparent;
        border: none;
    }}
    QHeaderView::section {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_MUTED']};
        border: none;
        border-bottom: 1px solid {c['BORDER_SUBTLE']};
        padding: 7px 8px;
        font-size: 10px;
        font-weight: 600;
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 8px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 8px;
    }}
    QTableCornerButton::section {{
        background: {c['SURFACE_SELECTED']};
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['BORDER_STRONG']};
        min-height: 28px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['TEXT_DISABLED']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
        background: transparent;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['BORDER_STRONG']};
        min-width: 28px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
        background: transparent;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}
    QMenu {{
        background: {c['SURFACE_CARD']};
        border: 1px solid {c['BORDER_STRONG']};
        border-radius: 9px;
        padding: 5px;
        color: {c['TEXT_SECONDARY']};
    }}
    QMenu::item {{
        padding: 7px 26px 7px 10px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_PRIMARY']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {c['BORDER_SUBTLE']};
        margin: 4px 8px;
    }}
    QToolButton {{
        background: transparent;
        border: none;
        border-radius: 8px;
        padding: 5px;
        color: {c['TEXT_MUTED']};
    }}
    QToolButton:hover {{
        background: {c['SURFACE_CARD_HOVER']};
        color: {c['TEXT_PRIMARY']};
    }}
    QToolButton::menu-indicator {{
        image: none;
    }}
    QToolTip {{
        background: {c['SURFACE_SELECTED']};
        color: {c['TEXT_PRIMARY']};
        border: 1px solid {c['BORDER_STRONG']};
        padding: 5px 8px;
        border-radius: 6px;
    }}
    QChartView {{
        background: transparent;
        border: none;
    }}
    QSplitter::handle {{
        background: transparent;
        width: 8px;
        height: 8px;
    }}
    QMessageBox, QFileDialog, QInputDialog {{
        background: {c['SURFACE_CARD']};
    }}
    QMessageBox QLabel {{
        color: {c['TEXT_SECONDARY']};
    }}
    QCalendarWidget QWidget {{
        alternate-background-color: {c['SURFACE_CARD']};
        background: {c['SURFACE_CARD']};
        color: {c['TEXT_SECONDARY']};
    }}
    QCalendarWidget QAbstractItemView:enabled {{
        background: {c['SURFACE_CARD']};
        selection-background-color: {c['ACCENT']};
        selection-color: {c['TEXT_ON_ACCENT']};
        color: {c['TEXT_SECONDARY']};
    }}
    QCalendarWidget QToolButton {{
        color: {c['TEXT_PRIMARY']};
        background: transparent;
    }}
    QFrame#Toast {{
        background: {c['SURFACE_CARD']};
        border: 1px solid {c['BORDER_STRONG']};
        border-radius: 10px;
    }}
    QLabel#ToastText {{
        color: {c['TEXT_PRIMARY']};
        font-size: 12px;
    }}
    QFrame#EmptyState {{
        background: transparent;
        border: 1px dashed {c['BORDER_STRONG']};
        border-radius: {radius['card']}px;
    }}
    QFrame#WindowRoot[maximized="true"] {{
        border-radius: 0px;
        border: none;
    }}
    QWidget#PageContent {{
        background: transparent;
    }}
    QLabel#TitleBarLabel {{
        color: {c['TEXT_DISABLED']};
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 1px;
    }}
    QLabel#TopPageTitle {{
        color: {c['TEXT_PRIMARY']};
        font-size: 21px;
        font-weight: 600;
    }}
    QLabel#WorkspaceName {{
        color: {c['TEXT_PRIMARY']};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#ProfileName {{
        color: {c['TEXT_PRIMARY']};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#ToggleTitle {{
        color: {c['TEXT_PRIMARY']};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#RecentPreview {{
        color: {c['TEXT_PRIMARY']};
        font-size: 12px;
        font-weight: 500;
    }}
    QFrame#RecentRow {{
        background: transparent;
        border: none;
    }}
    QLabel#StepBadge {{
        background: {c['ACCENT_SOFT']};
        color: {c['ACCENT']};
        border: 1px solid {c['BORDER_STRONG']};
        border-radius: 14px;
        font-size: 12px;
        font-weight: 700;
    }}
    """
    return qss.strip() + "\n"

