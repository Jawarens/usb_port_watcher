import os
from datetime import datetime
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QPushButton, QLabel, QFileDialog, QMessageBox, QMenu, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QAction, QIcon

from device_model import UsbDevice, UsbEvent
from win32_usb import UsbWatcherThread, enumerate_usb_devices
from ui.widgets import StatCard, FilterBar, StatusBadge
from ui.inspector_panel import InspectorPanel
from export_utils import export_events_to_csv, export_events_to_json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB Port Watcher — Real-Time Hardware & Driver Monitor")
        self.resize(1280, 800)
        self.setMinimumSize(950, 600)

        self.events: List[UsbEvent] = []
        self.active_devices: Dict[str, UsbDevice] = {}
        self.is_paused = False

        self._filter_text = ""
        self._filter_mode = "ALL"

        self._init_ui()

        # Start Win32 background USB listener thread
        self.watcher_thread = UsbWatcherThread(self)
        self.watcher_thread.device_connected.connect(self._on_device_connected)
        self.watcher_thread.device_disconnected.connect(self._on_device_disconnected)
        self.watcher_thread.device_changed.connect(self._on_device_changed)
        self.watcher_thread.log_message.connect(self._on_watcher_log)
        self.watcher_thread.start()

        # Initial device scan
        self.refresh_devices(initial=True)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # Header Frame
        header_frame = QWidget()
        header_frame.setObjectName("HeaderFrame")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(16)

        # Title & Indicator
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        app_title = QLabel("🔌 USB PORT WATCHER")
        app_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #38bdf8; letter-spacing: 0.8px;")
        
        self.lbl_status_indicator = QLabel("● Real-time Win32 PnP Hook Active")
        self.lbl_status_indicator.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 600;")
        title_box.addWidget(app_title)
        title_box.addWidget(self.lbl_status_indicator)
        h_layout.addLayout(title_box)

        h_layout.addStretch(1)

        # Stats Cards
        self.card_active = StatCard("Connected USB", "0", "#38bdf8")
        self.card_events = StatCard("Events Logged", "0", "#a78bfa")
        self.card_alerts = StatCard("Driver Alerts", "0", "#fb7185")
        h_layout.addWidget(self.card_active)
        h_layout.addWidget(self.card_events)
        h_layout.addWidget(self.card_alerts)

        # Control Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_pause = QPushButton("⏸️ Pause")
        self.btn_pause.setToolTip("Pause logging new USB events")
        self.btn_pause.clicked.connect(self._toggle_pause)
        btn_box.addWidget(self.btn_pause)

        self.btn_rescan = QPushButton("🔄 Rescan All")
        self.btn_rescan.setToolTip("Enumerate all connected USB devices now")
        self.btn_rescan.clicked.connect(self.refresh_devices)
        btn_box.addWidget(self.btn_rescan)

        self.btn_export = QPushButton("💾 Export Logs")
        self.btn_export.setToolTip("Export event log to CSV or JSON")
        self.btn_export.clicked.connect(self._show_export_menu)
        btn_box.addWidget(self.btn_export)

        self.btn_clear = QPushButton("🗑️ Clear Log")
        self.btn_clear.setObjectName("DangerButton")
        self.btn_clear.setToolTip("Clear the event log")
        self.btn_clear.clicked.connect(self._clear_logs)
        btn_box.addWidget(self.btn_clear)

        h_layout.addLayout(btn_box)
        root_layout.addWidget(header_frame)

        # Filter Bar
        self.filter_bar = FilterBar()
        self.filter_bar.filter_changed.connect(self._on_filter_changed)
        root_layout.addWidget(self.filter_bar)

        # Main Splitter: Left (Tabs) / Right (Inspector)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # Left Tab Widget
        self.tabs = QTabWidget()

        # Tab 1: Live Event Stream
        tab_events = QWidget()
        te_layout = QVBoxLayout(tab_events)
        te_layout.setContentsMargins(6, 6, 6, 6)

        self.table_events = QTableWidget(0, 7)
        self.table_events.setHorizontalHeaderLabels([
            "Timestamp", "Event", "Device Name", "VID : PID", "Port / Location", "Driver Health", "Manufacturer"
        ])
        self.table_events.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_events.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_events.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_events.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_events.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_events.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_events.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table_events.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_events.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_events.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_events.setAlternatingRowColors(True)
        self.table_events.verticalHeader().setVisible(False)
        self.table_events.itemSelectionChanged.connect(self._on_event_row_selected)
        self.table_events.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_events.customContextMenuRequested.connect(self._on_event_context_menu)
        te_layout.addWidget(self.table_events)

        self.tabs.addTab(tab_events, "📋 Live Event Log")

        # Tab 2: Connected Devices
        tab_devices = QWidget()
        td_layout = QVBoxLayout(tab_devices)
        td_layout.setContentsMargins(6, 6, 6, 6)

        self.table_devices = QTableWidget(0, 6)
        self.table_devices.setHorizontalHeaderLabels([
            "State", "Device Name", "VID : PID", "Port Location", "Driver Health", "Driver Provider"
        ])
        self.table_devices.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_devices.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_devices.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_devices.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_devices.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_devices.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_devices.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_devices.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_devices.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_devices.setAlternatingRowColors(True)
        self.table_devices.verticalHeader().setVisible(False)
        self.table_devices.itemSelectionChanged.connect(self._on_active_device_selected)
        self.table_devices.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_devices.customContextMenuRequested.connect(self._on_device_context_menu)
        td_layout.addWidget(self.table_devices)

        self.tabs.addTab(tab_devices, "⚡ Connected Devices")

        splitter.addWidget(self.tabs)

        # Right Inspector Panel
        self.inspector = InspectorPanel()
        self.inspector.setMinimumWidth(380)
        splitter.addWidget(self.inspector)

        # Splitter sizing ratio
        splitter.setSizes([780, 440])
        root_layout.addWidget(splitter)

        # Status Bar
        self.statusBar().showMessage("Ready • Monitoring USB hardware ports")

    def _toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.setText("▶️ Resume")
            self.lbl_status_indicator.setText("⏸️ Event Logging Paused")
            self.lbl_status_indicator.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: 600;")
        else:
            self.btn_pause.setText("⏸️ Pause")
            self.lbl_status_indicator.setText("● Real-time Win32 PnP Hook Active")
            self.lbl_status_indicator.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 600;")

    def refresh_devices(self, initial=False):
        """Enumerate active devices and refresh the devices list tab."""
        self.active_devices = enumerate_usb_devices()
        self._populate_active_devices_table()
        self._update_stat_cards()
        if not initial:
            self.statusBar().showMessage(f"Device tree refreshed: {len(self.active_devices)} devices detected.")

    def _update_stat_cards(self):
        active_count = len(self.active_devices)
        event_count = len(self.events)
        problem_count = sum(1 for d in self.active_devices.values() if d.problem_code != 0)

        self.card_active.set_value(active_count)
        self.card_events.set_value(event_count)
        self.card_alerts.set_value(problem_count)

    def _on_device_connected(self, event: UsbEvent):
        if self.is_paused:
            return
        self.events.append(event)
        self.active_devices[event.device.instance_id.upper()] = event.device
        self._add_event_row(event)
        self._populate_active_devices_table()
        self._update_stat_cards()
        self.statusBar().showMessage(f"🟢 Connected: {event.device.name} [{event.device.vid_pid_str}] at {event.timestamp_str}")

        # Auto-select newest event in inspector if nothing selected or user wants live follow
        self.inspector.set_device(event.device)

    def _on_device_disconnected(self, event: UsbEvent):
        if self.is_paused:
            return
        self.events.append(event)
        self.active_devices.pop(event.device.instance_id.upper(), None)
        self._add_event_row(event)
        self._populate_active_devices_table()
        self._update_stat_cards()
        self.statusBar().showMessage(f"🔴 Disconnected: {event.device.name} [{event.device.vid_pid_str}] at {event.timestamp_str}")
        self.inspector.set_device(event.device)

    def _on_device_changed(self, event: UsbEvent):
        if self.is_paused:
            return
        self.events.append(event)
        self.active_devices[event.device.instance_id.upper()] = event.device
        self._add_event_row(event)
        self._populate_active_devices_table()
        self._update_stat_cards()
        self.statusBar().showMessage(f"⚠️ Status Changed: {event.device.name} (Code {event.device.problem_code})")
        self.inspector.set_device(event.device)

    def _on_watcher_log(self, msg: str):
        self.statusBar().showMessage(msg)

    def _add_event_row(self, event: UsbEvent):
        # Check filters
        if not self._matches_filter(event.device, event.event_type):
            return

        row = self.table_events.rowCount()
        self.table_events.insertRow(row)

        dev = event.device

        # 0: Time
        t_item = QTableWidgetItem(event.timestamp_str)
        t_item.setData(Qt.ItemDataRole.UserRole, event)
        self.table_events.setItem(row, 0, t_item)

        # 1: Event Badge
        badge_type = "success" if event.event_type == "CONNECTED" else ("danger" if event.event_type == "DISCONNECTED" else "warning")
        badge = StatusBadge(event.event_type, badge_type)
        self.table_events.setCellWidget(row, 1, badge)

        # 2: Device Name
        n_item = QTableWidgetItem(dev.name)
        n_item.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.table_events.setItem(row, 2, n_item)

        # 3: VID:PID
        vp_item = QTableWidgetItem(dev.vid_pid_str)
        vp_item.setFont(QFont("Consolas", 9))
        self.table_events.setItem(row, 3, vp_item)

        # 4: Location
        loc_str = dev.location or "-"
        self.table_events.setItem(row, 4, QTableWidgetItem(loc_str))

        # 5: Driver Health
        prob_title, _ = dev.problem_description
        if dev.problem_code == 0:
            h_badge = StatusBadge("Normal", "success")
        elif dev.problem_code == 28:
            h_badge = StatusBadge("Missing Driver (28)", "warning")
        else:
            h_badge = StatusBadge(f"Error ({dev.problem_code})", "error_alert")
        self.table_events.setCellWidget(row, 5, h_badge)

        # 6: Manufacturer
        self.table_events.setItem(row, 6, QTableWidgetItem(dev.manufacturer or "-"))

        # Scroll to bottom
        self.table_events.scrollToBottom()

    def _populate_active_devices_table(self):
        self.table_devices.setRowCount(0)
        row = 0
        for dev in sorted(self.active_devices.values(), key=lambda d: d.name):
            if not self._matches_filter(dev, "CONNECTED"):
                continue

            self.table_devices.insertRow(row)

            # 0: State
            badge = StatusBadge("ONLINE", "success")
            self.table_devices.setCellWidget(row, 0, badge)

            # 1: Name
            n_item = QTableWidgetItem(dev.name)
            n_item.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            n_item.setData(Qt.ItemDataRole.UserRole, dev)
            self.table_devices.setItem(row, 1, n_item)

            # 2: VID:PID
            vp_item = QTableWidgetItem(dev.vid_pid_str)
            vp_item.setFont(QFont("Consolas", 9))
            self.table_devices.setItem(row, 2, vp_item)

            # 3: Port Location
            self.table_devices.setItem(row, 3, QTableWidgetItem(dev.location or "-"))

            # 4: Driver Health
            if dev.problem_code == 0:
                h_badge = StatusBadge("Healthy", "success")
            elif dev.problem_code == 28:
                h_badge = StatusBadge("Missing Driver (28)", "warning")
            else:
                h_badge = StatusBadge(f"Error ({dev.problem_code})", "error_alert")
            self.table_devices.setCellWidget(row, 4, h_badge)

            # 5: Provider
            drv_str = f"{dev.driver_provider} ({dev.driver_version})" if dev.driver_version else (dev.driver_provider or "-")
            self.table_devices.setItem(row, 5, QTableWidgetItem(drv_str))

            row += 1

    def _matches_filter(self, dev: UsbDevice, event_type: str) -> bool:
        # Check event filter mode
        if self._filter_mode == "CONNECTED" and event_type != "CONNECTED":
            return False
        if self._filter_mode == "DISCONNECTED" and event_type != "DISCONNECTED":
            return False
        if self._filter_mode == "ISSUES" and dev.problem_code == 0:
            return False

        # Check search text
        if self._filter_text:
            haystack = f"{dev.name} {dev.vid_pid_str} {dev.location} {dev.instance_id} {dev.manufacturer} {dev.driver_provider}".lower()
            if self._filter_text not in haystack:
                return False

        return True

    def _on_filter_changed(self, search_text: str, filter_mode: str):
        self._filter_text = search_text.lower()
        self._filter_mode = filter_mode
        self._reapply_filters()

    def _reapply_filters(self):
        # Re-populate events table
        self.table_events.setRowCount(0)
        for evt in self.events:
            self._add_event_row(evt)

        # Re-populate devices table
        self._populate_active_devices_table()

    def _on_event_row_selected(self):
        selected = self.table_events.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        item = self.table_events.item(row, 0)
        if item:
            event: UsbEvent = item.data(Qt.ItemDataRole.UserRole)
            if event:
                self.inspector.set_device(event.device)

    def _on_active_device_selected(self):
        selected = self.table_devices.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        item = self.table_devices.item(row, 1)
        if item:
            dev: UsbDevice = item.data(Qt.ItemDataRole.UserRole)
            if dev:
                self.inspector.set_device(dev)

    def _on_event_context_menu(self, pos):
        item = self.table_events.itemAt(pos)
        if not item:
            return
        row = item.row()
        time_item = self.table_events.item(row, 0)
        if not time_item:
            return
        event: UsbEvent = time_item.data(Qt.ItemDataRole.UserRole)
        if not event:
            return
        self._show_device_menu(event.device)

    def _on_device_context_menu(self, pos):
        item = self.table_devices.itemAt(pos)
        if not item:
            return
        row = item.row()
        name_item = self.table_devices.item(row, 1)
        if not name_item:
            return
        dev: UsbDevice = name_item.data(Qt.ItemDataRole.UserRole)
        if not dev:
            return
        self._show_device_menu(dev)

    def _show_device_menu(self, dev: UsbDevice):
        menu = QMenu(self)
        menu.setStyleSheet("background-color: #111827; color: #f8fafc; border: 1px solid #334155; padding: 4px;")

        act_copy_vid_pid = menu.addAction(f"📋 Copy VID:PID ({dev.vid_pid_str})")
        act_copy_hwid = menu.addAction("📋 Copy Primary Hardware ID")
        act_copy_inst = menu.addAction("📋 Copy Device Instance ID")
        menu.addSeparator()
        act_hunt = menu.addAction("🌐 Search on DeviceHunt USB DB")
        act_catalog = menu.addAction("🌐 Search Microsoft Update Catalog")
        act_google = menu.addAction("🔍 Search Google for Driver")

        action = menu.exec(self.cursor().pos())
        clipboard = self.topLevelWidget().windowHandle().screen() if False else None

        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()

        if action == act_copy_vid_pid:
            cb.setText(dev.vid_pid_str)
            self.statusBar().showMessage(f"Copied {dev.vid_pid_str} to clipboard.")
        elif action == act_copy_hwid:
            cb.setText(dev.primary_hardware_id)
            self.statusBar().showMessage("Copied Hardware ID to clipboard.")
        elif action == act_copy_inst:
            cb.setText(dev.instance_id)
            self.statusBar().showMessage("Copied Device Instance ID to clipboard.")
        elif action == act_hunt:
            self.inspector.current_device = dev
            self.inspector._open_devicehunt()
        elif action == act_catalog:
            self.inspector.current_device = dev
            self.inspector._open_catalog()
        elif action == act_google:
            self.inspector.current_device = dev
            self.inspector._open_google()

    def _show_export_menu(self):
        if not self.events:
            QMessageBox.information(self, "Export Logs", "No events have been logged yet to export.")
            return

        menu = QMenu(self)
        menu.setStyleSheet("background-color: #111827; color: #f8fafc; border: 1px solid #334155;")
        act_csv = menu.addAction("📄 Export as CSV...")
        act_json = menu.addAction("📦 Export as JSON...")

        action = menu.exec(self.btn_export.mapToGlobal(self.btn_export.rect().bottomLeft()))
        if action == act_csv:
            path, _ = QFileDialog.getSaveFileName(self, "Save USB Event Log (CSV)", "usb_events.csv", "CSV Files (*.csv)")
            if path:
                export_events_to_csv(path, self.events)
                self.statusBar().showMessage(f"Exported {len(self.events)} events to {path}")
        elif action == act_json:
            path, _ = QFileDialog.getSaveFileName(self, "Save USB Event Log (JSON)", "usb_events.json", "JSON Files (*.json)")
            if path:
                export_events_to_json(path, self.events)
                self.statusBar().showMessage(f"Exported {len(self.events)} events to {path}")

    def _clear_logs(self):
        if not self.events:
            return
        res = QMessageBox.question(
            self, "Clear Event Log", "Are you sure you want to clear all recorded USB events?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            self.events.clear()
            self.table_events.setRowCount(0)
            self._update_stat_cards()
            self.statusBar().showMessage("Event log cleared.")

    def closeEvent(self, event):
        if hasattr(self, "watcher_thread") and self.watcher_thread.isRunning():
            self.watcher_thread.stop()
        super().closeEvent(event)
