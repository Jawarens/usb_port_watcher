from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

# Windows Configuration Manager Problem Codes
CM_PROBLEM_CODES = {
    0: ("Normal", "Device is working properly."),
    1: ("Not Configured", "Device is not configured correctly (Code 1)."),
    3: ("Out of Memory", "Driver may be bad, or system is low on memory (Code 3)."),
    10: ("Failed to Start", "This device cannot start (Code 10). Often due to outdated drivers."),
    12: ("Resource Conflict", "This device cannot find enough free resources (Code 12)."),
    14: ("Reboot Required", "This device cannot work properly until computer is restarted (Code 14)."),
    16: ("Unrecognized", "Windows cannot identify all resources this device uses (Code 16)."),
    18: ("Reinstall Drivers", "Reinstall the drivers for this device (Code 18)."),
    19: ("Registry Error", "Windows cannot start this hardware device because its configuration info is incomplete or damaged (Code 19)."),
    21: ("Removing", "Windows is removing this device (Code 21)."),
    22: ("Disabled", "This device is disabled (Code 22)."),
    24: ("Not Present / Malfunction", "This device is not present, is not working properly, or does not have all its drivers installed (Code 24)."),
    28: ("Missing Driver", "The drivers for this device are not installed (Code 28)."),
    29: ("Firmware Disabled", "This device is disabled because firmware did not give it required resources (Code 29)."),
    31: ("Not Working", "This device is not working properly because Windows cannot load required drivers (Code 31)."),
    32: ("Driver Service Blocked", "A driver (service) for this device has been disabled (Code 32)."),
    37: ("Driver Init Failed", "Windows cannot initialize the device driver for this hardware (Code 37)."),
    38: ("Driver Already Loaded", "Windows cannot load device driver because previous instance is still in memory (Code 38)."),
    39: ("Driver Corrupted", "Windows cannot load the device driver for this hardware (Code 39)."),
    41: ("Driver Loaded but Unresolved", "Windows successfully loaded device driver but cannot find hardware device (Code 41)."),
    43: ("Hardware Failure / Stopped", "Windows stopped this device because it reported problems (Code 43). Common for unstable USB connections."),
    44: ("App Stopped Device", "An application or service shut down this device (Code 44)."),
    47: ("Safe Removal Prepared", "Windows cannot use this hardware device because it has been prepared for safe removal (Code 47)."),
    48: ("Blocked Driver", "The software for this device has been blocked from starting because it is known to have problems (Code 48)."),
    52: ("Unsigned Driver", "Windows cannot verify digital signature for drivers required for this device (Code 52)."),
}

@dataclass
class UsbDevice:
    instance_id: str                      # e.g. "USB\VID_0403&PID_6001\A50285BI"
    name: str                             # Friendly name or device desc
    description: str = ""
    hardware_ids: List[str] = field(default_factory=list)
    compatible_ids: List[str] = field(default_factory=list)
    manufacturer: str = ""
    device_class: str = ""
    service: str = ""
    location: str = ""                    # e.g. "Port_#0001.Hub_#0004"
    status_code: int = 0
    problem_code: int = 0
    driver_version: str = ""
    driver_date: str = ""
    driver_provider: str = ""
    matching_device_id: str = ""
    is_connected: bool = True
    vid: str = ""
    pid: str = ""

    def __post_init__(self):
        if not self.vid or not self.pid:
            self._extract_vid_pid()

    def _extract_vid_pid(self):
        # Parse VID / PID from hardware_ids or instance_id
        import re
        target = " ".join([self.instance_id] + self.hardware_ids)
        m = re.search(r"VID_([0-9A-Fa-f]{4})[&_]PID_([0-9A-Fa-f]{4})", target, re.IGNORECASE)
        if m:
            self.vid = m.group(1).upper()
            self.pid = m.group(2).upper()

    @property
    def vid_pid_str(self) -> str:
        if self.vid and self.pid:
            return f"{self.vid}:{self.pid}"
        return "Unknown"

    @property
    def primary_hardware_id(self) -> str:
        if self.hardware_ids:
            return self.hardware_ids[0]
        return self.instance_id

    @property
    def problem_description(self) -> tuple[str, str]:
        return CM_PROBLEM_CODES.get(self.problem_code, ("Unknown Error", f"Problem code {self.problem_code}"))

    @property
    def is_healthy(self) -> bool:
        return self.problem_code == 0

@dataclass
class UsbEvent:
    timestamp: datetime
    event_type: str                       # "CONNECTED", "DISCONNECTED", "DRIVER_CHANGED"
    device: UsbDevice
    raw_path: str = ""

    @property
    def timestamp_str(self) -> str:
        return self.timestamp.strftime("%H:%M:%S.%f")[:-3]
