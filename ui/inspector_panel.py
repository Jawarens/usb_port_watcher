import os
import subprocess
import urllib.parse
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QGridLayout, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

from device_model import UsbDevice
from ui.widgets import StatusBadge, CopyButton
from export_utils import generate_device_diagnostic_text

class InspectorPanel(QWidget):
    """
    Detailed inspection panel for selected USB device.
    Provides hardware identifiers, driver status, Windows problem codes,
    and 1-click driver hunting helpers.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_device: UsbDevice | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area container for small screens / long details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(14)

        # Header: Device Name & Status
        self.header_card = QFrame()
        self.header_card.setObjectName("InspectorCard")
        h_layout = QVBoxLayout(self.header_card)
        h_layout.setSpacing(6)

        title_row = QHBoxLayout()
        self.lbl_title = QLabel("Select a device to inspect")
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        self.lbl_title.setWordWrap(True)
        title_row.addWidget(self.lbl_title, stretch=1)

        self.status_badge = StatusBadge("NO SELECTION", "neutral")
        title_row.addWidget(self.status_badge)
        h_layout.addLayout(title_row)

        self.lbl_subtitle = QLabel("Plug in a USB device or click any entry in the event log.")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #94a3b8;")
        self.lbl_subtitle.setWordWrap(True)
        h_layout.addWidget(self.lbl_subtitle)

        self.layout.addWidget(self.header_card)

        # Diagnostic Alert Box (Visible if problem code != 0)
        self.alert_card = QFrame()
        self.alert_card.setObjectName("InspectorCard")
        self.alert_card.setStyleSheet("background-color: #2e1015; border: 1px solid #e11d48; border-radius: 8px; padding: 10px;")
        alert_layout = QVBoxLayout(self.alert_card)
        alert_layout.setSpacing(4)
        self.lbl_alert_title = QLabel("⚠️ DRIVER ISSUE DETECTED")
        self.lbl_alert_title.setStyleSheet("color: #fb7185; font-weight: 700; font-size: 13px;")
        self.lbl_alert_desc = QLabel("")
        self.lbl_alert_desc.setStyleSheet("color: #fda4af; font-size: 11px;")
        self.lbl_alert_desc.setWordWrap(True)
        alert_layout.addWidget(self.lbl_alert_title)
        alert_layout.addWidget(self.lbl_alert_desc)
        self.layout.addWidget(self.alert_card)
        self.alert_card.hide()

        # Section: Identifiers & Port Location
        self.id_card = QFrame()
        self.id_card.setObjectName("InspectorCard")
        id_layout = QVBoxLayout(self.id_card)
        id_layout.setSpacing(8)

        sec_id_lbl = QLabel("HARDWARE IDENTIFIERS & PORT")
        sec_id_lbl.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        id_layout.addWidget(sec_id_lbl)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        # VID:PID
        grid.addWidget(QLabel("VID : PID:"), 0, 0)
        self.lbl_vid_pid = QLabel("-")
        self.lbl_vid_pid.setStyleSheet("font-weight: 700; color: #e2e8f0; font-family: monospace;")
        grid.addWidget(self.lbl_vid_pid, 0, 1)
        self.btn_copy_vid_pid = CopyButton("", "Copy")
        grid.addWidget(self.btn_copy_vid_pid, 0, 2)

        # Location / Port
        grid.addWidget(QLabel("Port Location:"), 1, 0)
        self.lbl_loc = QLabel("-")
        self.lbl_loc.setStyleSheet("color: #94a3b8;")
        grid.addWidget(self.lbl_loc, 1, 1, 1, 2)

        # Device Instance ID
        grid.addWidget(QLabel("Device Instance ID:"), 2, 0)
        self.lbl_instance_id = QLabel("-")
        self.lbl_instance_id.setStyleSheet("color: #cbd5e1; font-family: monospace; font-size: 11px;")
        self.lbl_instance_id.setWordWrap(True)
        grid.addWidget(self.lbl_instance_id, 2, 1)
        self.btn_copy_instance_id = CopyButton("", "Copy")
        grid.addWidget(self.btn_copy_instance_id, 2, 2)

        # Primary Hardware ID
        grid.addWidget(QLabel("Hardware ID:"), 3, 0)
        self.lbl_hwid = QLabel("-")
        self.lbl_hwid.setStyleSheet("color: #cbd5e1; font-family: monospace; font-size: 11px;")
        self.lbl_hwid.setWordWrap(True)
        grid.addWidget(self.lbl_hwid, 3, 1)
        self.btn_copy_hwid = CopyButton("", "Copy")
        grid.addWidget(self.btn_copy_hwid, 3, 2)

        id_layout.addLayout(grid)
        self.layout.addWidget(self.id_card)

        # Section: Driver Details
        self.driver_card = QFrame()
        self.driver_card.setObjectName("InspectorCard")
        drv_layout = QVBoxLayout(self.driver_card)
        drv_layout.setSpacing(8)

        sec_drv_lbl = QLabel("DRIVER STATUS & PROVIDER")
        sec_drv_lbl.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        drv_layout.addWidget(sec_drv_lbl)

        dgrid = QGridLayout()
        dgrid.setHorizontalSpacing(10)
        dgrid.setVerticalSpacing(8)

        dgrid.addWidget(QLabel("Driver Provider:"), 0, 0)
        self.lbl_drv_provider = QLabel("-")
        dgrid.addWidget(self.lbl_drv_provider, 0, 1)

        dgrid.addWidget(QLabel("Driver Version:"), 1, 0)
        self.lbl_drv_version = QLabel("-")
        dgrid.addWidget(self.lbl_drv_version, 1, 1)

        dgrid.addWidget(QLabel("Driver Date:"), 2, 0)
        self.lbl_drv_date = QLabel("-")
        dgrid.addWidget(self.lbl_drv_date, 2, 1)

        dgrid.addWidget(QLabel("Matching INF ID:"), 3, 0)
        self.lbl_matching_inf = QLabel("-")
        self.lbl_matching_inf.setWordWrap(True)
        dgrid.addWidget(self.lbl_matching_inf, 3, 1)

        drv_layout.addLayout(dgrid)
        self.layout.addWidget(self.driver_card)

        # Section: Driver Lookup & Actions
        self.action_card = QFrame()
        self.action_card.setObjectName("InspectorCard")
        act_layout = QVBoxLayout(self.action_card)
        act_layout.setSpacing(10)

        sec_act_lbl = QLabel("DRIVER HUNTING & TOOLS")
        sec_act_lbl.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        act_layout.addWidget(sec_act_lbl)

        # Button row 1: Online Databases
        row1 = QHBoxLayout()
        self.btn_devicehunt = QPushButton("🌐 DeviceHunt USB DB")
        self.btn_devicehunt.setObjectName("ActionButton")
        self.btn_devicehunt.setToolTip("Lookup Vendor and Product ID in DeviceHunt database")
        self.btn_devicehunt.clicked.connect(self._open_devicehunt)
        row1.addWidget(self.btn_devicehunt)

        self.btn_catalog = QPushButton("🌐 MS Update Catalog")
        self.btn_catalog.setObjectName("ActionButton")
        self.btn_catalog.setToolTip("Search Microsoft Update Catalog for official driver CABs")
        self.btn_catalog.clicked.connect(self._open_catalog)
        row1.addWidget(self.btn_catalog)
        act_layout.addLayout(row1)

        # Button row 2: Google & Device Manager
        row2 = QHBoxLayout()
        self.btn_google = QPushButton("🔍 Google Driver Search")
        self.btn_google.setObjectName("ActionButton")
        self.btn_google.setToolTip("Search Google for this exact Hardware ID driver")
        self.btn_google.clicked.connect(self._open_google)
        row2.addWidget(self.btn_google)

        self.btn_devmgmt = QPushButton("⚙️ Device Manager")
        self.btn_devmgmt.setObjectName("ActionButton")
        self.btn_devmgmt.setToolTip("Open Windows Device Manager")
        self.btn_devmgmt.clicked.connect(self._open_devmgmt)
        row2.addWidget(self.btn_devmgmt)
        act_layout.addLayout(row2)

        # Full Diagnostic Report Copy Button
        self.btn_copy_report = CopyButton("", "Copy Full Diagnostic Report")
        self.btn_copy_report.setObjectName("PrimaryButton")
        act_layout.addWidget(self.btn_copy_report)

        self.layout.addWidget(self.action_card)
        self.layout.addStretch(1)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def set_device(self, dev: UsbDevice | None):
        self.current_device = dev
        if not dev:
            self.lbl_title.setText("No Device Selected")
            self.lbl_subtitle.setText("Select a device from the list or event log.")
            self.status_badge.setText("IDLE")
            self.status_badge.set_badge_type("neutral")
            self.alert_card.hide()
            self.lbl_vid_pid.setText("-")
            self.lbl_loc.setText("-")
            self.lbl_instance_id.setText("-")
            self.lbl_hwid.setText("-")
            self.lbl_drv_provider.setText("-")
            self.lbl_drv_version.setText("-")
            self.lbl_drv_date.setText("-")
            self.lbl_matching_inf.setText("-")
            self.btn_copy_vid_pid.set_copy_text("")
            self.btn_copy_instance_id.set_copy_text("")
            self.btn_copy_hwid.set_copy_text("")
            self.btn_copy_report.set_copy_text("")
            return

        # Title & Subtitle
        self.lbl_title.setText(dev.name)
        mfg = dev.manufacturer or "Generic / Unknown Manufacturer"
        cls = dev.device_class or "USB"
        self.lbl_subtitle.setText(f"Manufacturer: {mfg} • Class: {cls}")

        # Status Badge & Alert Box
        prob_title, prob_desc = dev.problem_description
        if not dev.is_connected:
            self.status_badge.setText("🔴 DISCONNECTED")
            self.status_badge.set_badge_type("danger")
            self.alert_card.hide()
        elif dev.problem_code == 0:
            self.status_badge.setText("🟢 WORKING NORMALLY")
            self.status_badge.set_badge_type("success")
            self.alert_card.hide()
        elif dev.problem_code == 28:
            self.status_badge.setText("⚠️ CODE 28: DRIVER MISSING")
            self.status_badge.set_badge_type("warning")
            self.lbl_alert_title.setText("⚠️ CODE 28: DRIVER MISSING")
            self.lbl_alert_desc.setText("Windows has no driver installed for this USB device. Use the driver search buttons below to obtain compatible drivers.")
            self.alert_card.show()
        else:
            self.status_badge.setText(f"⚠️ ERROR CODE {dev.problem_code}")
            self.status_badge.set_badge_type("error_alert")
            self.lbl_alert_title.setText(f"⚠️ {prob_title.upper()} (CODE {dev.problem_code})")
            self.lbl_alert_desc.setText(prob_desc)
            self.alert_card.show()

        # Identifiers
        self.lbl_vid_pid.setText(dev.vid_pid_str)
        self.lbl_loc.setText(dev.location or "Root Hub / Internal Port")
        self.lbl_instance_id.setText(dev.instance_id)
        self.lbl_hwid.setText(dev.primary_hardware_id)

        self.btn_copy_vid_pid.set_copy_text(dev.vid_pid_str)
        self.btn_copy_instance_id.set_copy_text(dev.instance_id)
        self.btn_copy_hwid.set_copy_text(dev.primary_hardware_id)

        # Driver details
        self.lbl_drv_provider.setText(dev.driver_provider or "No driver loaded / Missing")
        self.lbl_drv_version.setText(dev.driver_version or "N/A")
        self.lbl_drv_date.setText(dev.driver_date or "N/A")
        self.lbl_matching_inf.setText(dev.matching_device_id or "N/A")

        # Full diagnostic report
        report_text = generate_device_diagnostic_text(dev)
        self.btn_copy_report.set_copy_text(report_text)

    def _open_devicehunt(self):
        if not self.current_device:
            return
        vid = self.current_device.vid or ""
        pid = self.current_device.pid or ""
        if vid and pid:
            url = f"https://devicehunt.com/search/type/usb/vendor/{vid}/device/{pid}"
        elif vid:
            url = f"https://devicehunt.com/search/type/usb/vendor/{vid}"
        else:
            url = "https://devicehunt.com/all-usb-vendors"
        QDesktopServices.openUrl(QUrl(url))

    def _open_catalog(self):
        if not self.current_device:
            return
        query = self.current_device.primary_hardware_id or self.current_device.vid_pid_str
        encoded = urllib.parse.quote(query)
        url = f"https://www.catalog.update.microsoft.com/Search.aspx?q={encoded}"
        QDesktopServices.openUrl(QUrl(url))

    def _open_google(self):
        if not self.current_device:
            return
        query = f"{self.current_device.primary_hardware_id} driver"
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}"
        QDesktopServices.openUrl(QUrl(url))

    def _open_devmgmt(self):
        try:
            subprocess.Popen(["devmgmt.msc"], shell=True)
        except Exception:
            pass
