from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QFrame, QLineEdit, QRadioButton, QButtonGroup, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont

class StatusBadge(QLabel):
    """Clean pill badge with color coding for connection state and Windows problem codes."""
    def __init__(self, text: str, badge_type: str = "success", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(22)
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.set_badge_type(badge_type)

    def set_badge_type(self, badge_type: str):
        # badge_type: "success", "danger", "warning", "info", "neutral"
        styles = {
            "success": "background-color: #064e3b; color: #34d399; border: 1px solid #059669; border-radius: 11px; padding: 2px 8px;",
            "danger": "background-color: #450a0a; color: #f87171; border: 1px solid #dc2626; border-radius: 11px; padding: 2px 8px;",
            "warning": "background-color: #451a03; color: #fbbf24; border: 1px solid #d97706; border-radius: 11px; padding: 2px 8px;",
            "error_alert": "background-color: #4c0519; color: #fb7185; border: 1px solid #e11d48; border-radius: 11px; padding: 2px 8px;",
            "info": "background-color: #082f49; color: #38bdf8; border: 1px solid #0284c7; border-radius: 11px; padding: 2px 8px;",
            "neutral": "background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 11px; padding: 2px 8px;",
        }
        self.setStyleSheet(styles.get(badge_type, styles["neutral"]))


class CopyButton(QPushButton):
    """Button that copies text to clipboard and flashes a confirmation."""
    def __init__(self, text_to_copy: str = "", label: str = "Copy", parent=None):
        super().__init__(f"📋 {label}", parent)
        self.text_to_copy = text_to_copy
        self.original_label = f"📋 {label}"
        self.setObjectName("ActionButton")
        self.clicked.connect(self._copy_action)

    def set_copy_text(self, text: str):
        self.text_to_copy = text

    def _copy_action(self):
        if not self.text_to_copy:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_to_copy)
        self.setText("✓ Copied!")
        self.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669;")
        QTimer.singleShot(1400, self._reset_label)

    def _reset_label(self):
        self.setText(self.original_label)
        self.setStyleSheet("")


class StatCard(QFrame):
    """Top statistic card widget."""
    def __init__(self, title: str, initial_value: str = "0", accent_color: str = "#38bdf8", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")

        self.val_lbl = QLabel(initial_value)
        self.val_lbl.setStyleSheet(f"color: {accent_color}; font-size: 18px; font-weight: 800;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.val_lbl)

    def set_value(self, val: str | int):
        self.val_lbl.setText(str(val))


class FilterBar(QWidget):
    """Search and filter control widget."""
    filter_changed = pyqtSignal(str, str) # (search_text, filter_mode)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter by Name, VID:PID (e.g. 0403:6001), Port, or Driver...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._emit_change)
        layout.addWidget(self.search_input, stretch=2)

        # Filter mode buttons
        self.btn_group = QButtonGroup(self)
        self.radio_all = QRadioButton("All Events")
        self.radio_connected = QRadioButton("🟢 Connected")
        self.radio_disconnected = QRadioButton("🔴 Disconnected")
        self.radio_issues = QRadioButton("⚠️ Driver Issues Only")

        self.radio_all.setChecked(True)
        self.btn_group.addButton(self.radio_all, 0)
        self.btn_group.addButton(self.radio_connected, 1)
        self.btn_group.addButton(self.radio_disconnected, 2)
        self.btn_group.addButton(self.radio_issues, 3)

        self.btn_group.buttonClicked.connect(self._emit_change)

        for btn in (self.radio_all, self.radio_connected, self.radio_disconnected, self.radio_issues):
            layout.addWidget(btn)

    def _emit_change(self):
        txt = self.search_input.text().strip()
        checked_id = self.btn_group.checkedId()
        mode_map = {0: "ALL", 1: "CONNECTED", 2: "DISCONNECTED", 3: "ISSUES"}
        self.filter_changed.emit(txt, mode_map.get(checked_id, "ALL"))
