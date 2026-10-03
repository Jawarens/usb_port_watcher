"""
Modern Dark Theme Stylesheet for USB Port Watcher.
Curated slate / cyan / emerald / amber color palette.
"""

DARK_STYLESHEET = """
QMainWindow {
    background-color: #0b0f17;
    color: #e2e8f0;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
}

QWidget {
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
    color: #e2e8f0;
}

/* ToolBar & Header Containers */
#HeaderFrame {
    background-color: #111827;
    border-bottom: 1px solid #1f2937;
    padding: 8px 16px;
}

#StatCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
}

#InspectorCard {
    background-color: #131d2e;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 12px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0d131f;
    border-radius: 0 0 8px 8px;
}

QTabBar::tab {
    background: #111827;
    color: #94a3b8;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #1f2937;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background: #0d131f;
    color: #38bdf8;
    border-top: 2px solid #38bdf8;
    border-bottom: 1px solid #0d131f;
}

QTabBar::tab:hover:!selected {
    background: #1a2234;
    color: #f1f5f9;
}

/* Tables */
QTableWidget, QTableView, QTreeWidget {
    background-color: #0d131f;
    alternate-background-color: #111827;
    color: #f1f5f9;
    border: 1px solid #1e293b;
    border-radius: 8px;
    gridline-color: #1a2333;
    font-size: 12px;
    selection-background-color: #1e3a5f;
    selection-color: #ffffff;
    outline: none;
}

QTableWidget::item, QTreeWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #151f30;
}

QTableWidget::item:selected, QTreeWidget::item:selected {
    background-color: #1e3a5f;
    color: #38bdf8;
}

QTableWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {
    background-color: #162032;
}

QHeaderView::section {
    background-color: #131c2d;
    color: #94a3b8;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #1f2e46;
}

/* Inputs & Search */
QLineEdit {
    background-color: #131c2d;
    border: 1px solid #24344d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f8fafc;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #162238;
}

/* Buttons */
QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #f1f5f9;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2b3952;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #182234;
}

QPushButton:disabled {
    background-color: #141b27;
    color: #475569;
    border-color: #1f2937;
}

/* Primary Accent Button */
QPushButton#PrimaryButton {
    background-color: #0284c7;
    border: 1px solid #0ea5e9;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background-color: #0369a1;
}

/* Danger / Clear Button */
QPushButton#DangerButton:hover {
    background-color: #7f1d1d;
    border-color: #dc2626;
    color: #fca5a5;
}

/* Action Link / Tool Buttons */
QPushButton#ActionButton {
    background-color: #162238;
    border: 1px solid #223755;
    color: #38bdf8;
    font-weight: 500;
    padding: 5px 10px;
    border-radius: 5px;
}

QPushButton#ActionButton:hover {
    background-color: #1e3355;
    border-color: #38bdf8;
    color: #7dd3fc;
}

/* Filter Radio/Check Buttons */
QRadioButton, QCheckBox {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 500;
    spacing: 6px;
}

QRadioButton:checked, QCheckBox:checked {
    color: #38bdf8;
    font-weight: 600;
}

/* Splitter */
QSplitter::handle {
    background-color: #182234;
}

QSplitter::handle:horizontal {
    width: 3px;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #0d131f;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #24344d;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #3b5072;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #0d131f;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #24344d;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #3b5072;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #0b0f17;
    border-top: 1px solid #182234;
    color: #64748b;
    font-size: 11px;
}
"""
