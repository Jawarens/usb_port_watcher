import ctypes
from ctypes import wintypes
import re
from datetime import datetime
from typing import Dict, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from device_model import UsbDevice, UsbEvent

# Win32 Constants
DIGCF_PRESENT = 0x00000002
DIGCF_ALLCLASSES = 0x00000004
DIGCF_DEVICEINTERFACE = 0x00000010

SPDRP_DEVICEDESC = 0x00000000
SPDRP_HARDWAREID = 0x00000001
SPDRP_COMPATIBLEIDS = 0x00000002
SPDRP_SERVICE = 0x00000004
SPDRP_CLASS = 0x00000007
SPDRP_CLASSGUID = 0x00000008
SPDRP_DRIVER = 0x00000009
SPDRP_CONFIGFLAGS = 0x0000000A
SPDRP_MFG = 0x0000000B
SPDRP_FRIENDLYNAME = 0x0000000C
SPDRP_LOCATION_INFORMATION = 0x0000000D

DICS_FLAG_GLOBAL = 0x00000001
DIREG_DEV = 0x00000001
DIREG_DRV = 0x00000002
KEY_READ = 0x20019

WM_DEVICECHANGE = 0x0219
WM_USER_STOP = 0x0400 + 100
DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEREMOVECOMPLETE = 0x8004
DBT_DEVNODES_CHANGED = 0x0007
DBT_DEVTYP_DEVICEINTERFACE = 0x00000005

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

# GUID_DEVINTERFACE_USB_DEVICE {A5DCBF10-6530-11D2-901F-00C04FB951ED}
GUID_USB_DEVICE = GUID(
    0xA5DCBF10, 0x6530, 0x11D2,
    (wintypes.BYTE * 8)(0x90, 0x1F, 0x00, 0xC0, 0x4F, 0xB9, 0x51, 0xED)
)

class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ctypes.POINTER(wintypes.ULONG)),
    ]

class DEV_BROADCAST_HDR(ctypes.Structure):
    _fields_ = [
        ("dbch_size", wintypes.DWORD),
        ("dbch_devicetype", wintypes.DWORD),
        ("dbch_reserved", wintypes.DWORD)
    ]

class DEV_BROADCAST_DEVICEINTERFACE_W(ctypes.Structure):
    _fields_ = [
        ("dbcc_size", wintypes.DWORD),
        ("dbcc_devicetype", wintypes.DWORD),
        ("dbcc_reserved", wintypes.DWORD),
        ("dbcc_classguid", GUID),
        ("dbcc_name", wintypes.WCHAR * 260)
    ]

# Setup DLL bindings with explicit 64-bit argtypes
setupapi = ctypes.windll.setupapi
cfgmgr32 = ctypes.windll.cfgmgr32
user32 = ctypes.windll.user32
advapi32 = ctypes.windll.advapi32

HDEVINFO = ctypes.c_void_p

setupapi.SetupDiGetClassDevsW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]
setupapi.SetupDiGetClassDevsW.restype = HDEVINFO

setupapi.SetupDiEnumDeviceInfo.argtypes = [HDEVINFO, wintypes.DWORD, ctypes.POINTER(SP_DEVINFO_DATA)]
setupapi.SetupDiEnumDeviceInfo.restype = wintypes.BOOL

setupapi.SetupDiDestroyDeviceInfoList.argtypes = [HDEVINFO]
setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

setupapi.SetupDiGetDeviceRegistryPropertyW.argtypes = [
    HDEVINFO, ctypes.POINTER(SP_DEVINFO_DATA), wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
]
setupapi.SetupDiGetDeviceRegistryPropertyW.restype = wintypes.BOOL

setupapi.SetupDiOpenDevRegKey.argtypes = [
    HDEVINFO, ctypes.POINTER(SP_DEVINFO_DATA), wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD
]
setupapi.SetupDiOpenDevRegKey.restype = wintypes.HKEY

cfgmgr32.CM_Get_Device_IDW.argtypes = [wintypes.DWORD, wintypes.LPWSTR, wintypes.ULONG, wintypes.ULONG]
cfgmgr32.CM_Get_Device_IDW.restype = wintypes.DWORD

cfgmgr32.CM_Get_DevNode_Status.argtypes = [ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, wintypes.ULONG]
cfgmgr32.CM_Get_DevNode_Status.restype = wintypes.DWORD

advapi32.RegQueryValueExW.argtypes = [
    wintypes.HKEY, wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)
]
advapi32.RegQueryValueExW.restype = wintypes.LONG

advapi32.RegCloseKey.argtypes = [wintypes.HKEY]
advapi32.RegCloseKey.restype = wintypes.LONG

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_int64

user32.RegisterDeviceNotificationW.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.DWORD]
user32.RegisterDeviceNotificationW.restype = ctypes.c_void_p

user32.UnregisterDeviceNotification.argtypes = [ctypes.c_void_p]
user32.UnregisterDeviceNotification.restype = wintypes.BOOL

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL


def _get_registry_string(hdev: HDEVINFO, devinfo: SP_DEVINFO_DATA, prop_id: int) -> str:
    buf_size = wintypes.DWORD(0)
    setupapi.SetupDiGetDeviceRegistryPropertyW(hdev, ctypes.byref(devinfo), prop_id, None, None, 0, ctypes.byref(buf_size))
    if buf_size.value > 0:
        buf = ctypes.create_unicode_buffer(buf_size.value // 2 + 2)
        if setupapi.SetupDiGetDeviceRegistryPropertyW(
            hdev, ctypes.byref(devinfo), prop_id, None, ctypes.cast(buf, ctypes.c_void_p), buf_size, None
        ):
            return buf.value.strip()
    return ""


def _get_registry_multi_string(hdev: HDEVINFO, devinfo: SP_DEVINFO_DATA, prop_id: int) -> List[str]:
    buf_size = wintypes.DWORD(0)
    setupapi.SetupDiGetDeviceRegistryPropertyW(hdev, ctypes.byref(devinfo), prop_id, None, None, 0, ctypes.byref(buf_size))
    if buf_size.value > 0:
        chars_count = buf_size.value // 2 + 2
        buf = ctypes.create_unicode_buffer(chars_count)
        if setupapi.SetupDiGetDeviceRegistryPropertyW(
            hdev, ctypes.byref(devinfo), prop_id, None, ctypes.cast(buf, ctypes.c_void_p), buf_size, None
        ):
            full_str = "".join([c for c in buf])
            parts = [p.strip() for p in full_str.split("\x00") if p.strip()]
            return parts
    return []


def _read_driver_registry_info(hdev: HDEVINFO, devinfo: SP_DEVINFO_DATA) -> dict:
    info = {
        "DriverVersion": "",
        "DriverDate": "",
        "DriverProviderName": "",
        "MatchingDeviceId": "",
    }
    hkey = setupapi.SetupDiOpenDevRegKey(hdev, ctypes.byref(devinfo), DICS_FLAG_GLOBAL, 0, DIREG_DRV, KEY_READ)
    if hkey and hkey != -1:
        for val_name in ["DriverVersion", "DriverDate", "DriverProviderName", "MatchingDeviceId", "ProviderName"]:
            buf_size = wintypes.DWORD(0)
            dwType = wintypes.DWORD(0)
            advapi32.RegQueryValueExW(hkey, val_name, None, ctypes.byref(dwType), None, ctypes.byref(buf_size))
            if buf_size.value > 0:
                buf = ctypes.create_unicode_buffer(buf_size.value // 2 + 2)
                if advapi32.RegQueryValueExW(
                    hkey, val_name, None, ctypes.byref(dwType), ctypes.cast(buf, ctypes.c_void_p), ctypes.byref(buf_size)
                ) == 0:
                    val = buf.value.strip()
                    if val_name == "ProviderName" and not info.get("DriverProviderName"):
                        info["DriverProviderName"] = val
                    else:
                        info[val_name] = val
        advapi32.RegCloseKey(hkey)
    return info


def enumerate_usb_devices() -> Dict[str, UsbDevice]:
    """Enumerate all currently connected USB devices on the system."""
    devices: Dict[str, UsbDevice] = {}
    hdev = setupapi.SetupDiGetClassDevsW(None, "USB", None, DIGCF_PRESENT | DIGCF_ALLCLASSES)
    if not hdev or hdev == -1:
        return devices

    devinfo = SP_DEVINFO_DATA()
    devinfo.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

    idx = 0
    try:
        while setupapi.SetupDiEnumDeviceInfo(hdev, idx, ctypes.byref(devinfo)):
            idx += 1
            # Device Instance ID
            dev_id_buf = ctypes.create_unicode_buffer(512)
            cfgmgr32.CM_Get_Device_IDW(devinfo.DevInst, dev_id_buf, 512, 0)
            instance_id = dev_id_buf.value.strip()

            # Status & Problem Code
            pulStatus = wintypes.DWORD()
            pulProblemNumber = wintypes.DWORD()
            cr_stat = cfgmgr32.CM_Get_DevNode_Status(
                ctypes.byref(pulStatus), ctypes.byref(pulProblemNumber), devinfo.DevInst, 0
            )
            status_code = pulStatus.value if cr_stat == 0 else 0
            problem_code = pulProblemNumber.value if cr_stat == 0 else 0

            desc = _get_registry_string(hdev, devinfo, SPDRP_DEVICEDESC)
            fname = _get_registry_string(hdev, devinfo, SPDRP_FRIENDLYNAME)
            mfg = _get_registry_string(hdev, devinfo, SPDRP_MFG)
            hwids = _get_registry_multi_string(hdev, devinfo, SPDRP_HARDWAREID)
            comp_ids = _get_registry_multi_string(hdev, devinfo, SPDRP_COMPATIBLEIDS)
            loc = _get_registry_string(hdev, devinfo, SPDRP_LOCATION_INFORMATION)
            service = _get_registry_string(hdev, devinfo, SPDRP_SERVICE)
            dev_class = _get_registry_string(hdev, devinfo, SPDRP_CLASS)

            # Read driver info
            drv_info = _read_driver_registry_info(hdev, devinfo)

            name = fname or desc or "USB Device"

            device = UsbDevice(
                instance_id=instance_id,
                name=name,
                description=desc,
                hardware_ids=hwids,
                compatible_ids=comp_ids,
                manufacturer=mfg,
                device_class=dev_class or "USB",
                service=service,
                location=loc,
                status_code=status_code,
                problem_code=problem_code,
                driver_version=drv_info.get("DriverVersion", ""),
                driver_date=drv_info.get("DriverDate", ""),
                driver_provider=drv_info.get("DriverProviderName", ""),
                matching_device_id=drv_info.get("MatchingDeviceId", ""),
                is_connected=True,
            )

            devices[instance_id.upper()] = device
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(hdev)

    return devices


class UsbWatcherThread(QThread):
    """
    Background worker that runs a native Win32 window message loop
    to catch DBT_DEVICEARRIVAL and DBT_DEVICEREMOVECOMPLETE with microsecond latency.
    """
    device_connected = pyqtSignal(object)       # UsbEvent
    device_disconnected = pyqtSignal(object)    # UsbEvent
    device_changed = pyqtSignal(object)         # UsbEvent
    log_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._hwnd: Optional[int] = None
        self._hNotify: Optional[int] = None
        self._wnd_proc_ref = None
        self._known_devices: Dict[str, UsbDevice] = {}

    def run(self):
        self._running = True
        self._known_devices = enumerate_usb_devices()

        # Define Window Class
        class WNDCLASSEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
                ("hIconSm", wintypes.HICON),
            ]

        def _wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_DEVICECHANGE:
                self._handle_device_change(wparam, lparam)
                return 1
            elif msg == WM_USER_STOP:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc_ref = WNDPROC(_wnd_proc)
        class_name = f"USBWatcher_Class_{id(self)}"

        wndclass = WNDCLASSEXW()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wndclass.lpfnWndProc = self._wnd_proc_ref
        wndclass.lpszClassName = class_name

        atom = user32.RegisterClassExW(ctypes.byref(wndclass))
        if not atom:
            self.log_message.emit("Failed to register window class for USB watcher.")
            return

        # Create message-only or utility window
        self._hwnd = user32.CreateWindowExW(
            0, class_name, "USBWatcher_Window", 0, 0, 0, 0, 0, 0, 0, 0, 0
        )
        if not self._hwnd:
            self.log_message.emit("Failed to create message window for USB watcher.")
            return

        # Register for USB device interface notifications
        filter_buf = DEV_BROADCAST_DEVICEINTERFACE_W()
        filter_buf.dbcc_size = ctypes.sizeof(DEV_BROADCAST_DEVICEINTERFACE_W)
        filter_buf.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        filter_buf.dbcc_classguid = GUID_USB_DEVICE

        self._hNotify = user32.RegisterDeviceNotificationW(
            self._hwnd,
            ctypes.byref(filter_buf),
            0x00000000 # DEVICE_NOTIFY_WINDOW_HANDLE
        )

        self.log_message.emit(f"USB Watcher active. Monitoring USB hardware events...")

        # Run Win32 Message Loop
        class MSG(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt_x", wintypes.LONG),
                ("pt_y", wintypes.LONG),
            ]

        msg = MSG()
        pmsg = ctypes.byref(msg)
        while self._running:
            bRet = user32.GetMessageW(pmsg, None, 0, 0)
            if bRet == 0 or bRet == -1: # WM_QUIT or Error
                break
            user32.TranslateMessage(pmsg)
            user32.DispatchMessageW(pmsg)

        # Cleanup
        if self._hNotify:
            user32.UnregisterDeviceNotification(self._hNotify)
            self._hNotify = None
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)
            self._hwnd = None
        user32.UnregisterClassW(class_name, None)

    def _handle_device_change(self, wparam: int, lparam: int):
        now = datetime.now()
        raw_path = ""
        action = None

        if wparam == DBT_DEVICEARRIVAL:
            action = "CONNECTED"
        elif wparam == DBT_DEVICEREMOVECOMPLETE:
            action = "DISCONNECTED"
        elif wparam == DBT_DEVNODES_CHANGED:
            action = "CHANGED"

        if not action:
            return

        if lparam:
            try:
                hdr = DEV_BROADCAST_HDR.from_address(lparam)
                if hdr.dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                    dev_iface = DEV_BROADCAST_DEVICEINTERFACE_W.from_address(lparam)
                    raw_path = dev_iface.dbcc_name
            except Exception:
                pass

        # Give Windows PnP driver stack a brief moment (~120ms) to update registry / status
        self.msleep(120)
        current_devices = enumerate_usb_devices()

        if action == "CONNECTED":
            new_ids = set(current_devices.keys()) - set(self._known_devices.keys())
            if new_ids:
                for inst_id in new_ids:
                    dev = current_devices[inst_id]
                    self._known_devices[inst_id] = dev
                    evt = UsbEvent(timestamp=now, event_type="CONNECTED", device=dev, raw_path=raw_path)
                    self.device_connected.emit(evt)
            elif raw_path:
                # Fallback: extract VID/PID from raw_path and emit
                parsed_dev = self._find_or_create_device_from_path(raw_path, current_devices)
                evt = UsbEvent(timestamp=now, event_type="CONNECTED", device=parsed_dev, raw_path=raw_path)
                self.device_connected.emit(evt)
            else:
                # General rescan
                self._emit_snapshot_diff(current_devices, now)

        elif action == "DISCONNECTED":
            removed_ids = set(self._known_devices.keys()) - set(current_devices.keys())
            if removed_ids:
                for inst_id in removed_ids:
                    dev = self._known_devices.pop(inst_id)
                    dev.is_connected = False
                    evt = UsbEvent(timestamp=now, event_type="DISCONNECTED", device=dev, raw_path=raw_path)
                    self.device_disconnected.emit(evt)
            elif raw_path:
                parsed_dev = self._find_or_create_device_from_path(raw_path, self._known_devices)
                parsed_dev.is_connected = False
                evt = UsbEvent(timestamp=now, event_type="DISCONNECTED", device=parsed_dev, raw_path=raw_path)
                self.device_disconnected.emit(evt)
            else:
                self._emit_snapshot_diff(current_devices, now)

        elif action == "CHANGED":
            # Check for driver or status changes in existing devices
            for inst_id, cur_dev in current_devices.items():
                if inst_id in self._known_devices:
                    prev_dev = self._known_devices[inst_id]
                    if (
                        cur_dev.problem_code != prev_dev.problem_code
                        or cur_dev.driver_version != prev_dev.driver_version
                        or cur_dev.status_code != prev_dev.status_code
                    ):
                        self._known_devices[inst_id] = cur_dev
                        evt = UsbEvent(timestamp=now, event_type="DRIVER_CHANGED", device=cur_dev, raw_path=raw_path)
                        self.device_changed.emit(evt)
            # Update snapshot
            self._known_devices = current_devices

    def _find_or_create_device_from_path(self, raw_path: str, device_pool: Dict[str, UsbDevice]) -> UsbDevice:
        # raw_path looks like "\\?\USB#VID_0403&PID_6001#A50285BI#{a5dcbf10-6530-11d2-901f-00c04fb951ed}"
        norm_path = raw_path.upper().replace("\\\\?\\", "").replace("#", "\\")
        for inst_id, dev in device_pool.items():
            if inst_id.upper() in norm_path or norm_path in inst_id.upper():
                return dev

        # Extract VID/PID
        m = re.search(r"VID_([0-9A-F]{4})[&_]PID_([0-9A-F]{4})", raw_path, re.IGNORECASE)
        vid = m.group(1).upper() if m else ""
        pid = m.group(2).upper() if m else ""

        inst_parts = raw_path.replace("\\\\?\\", "").split("#{")
        inst_id = inst_parts[0].replace("#", "\\") if inst_parts else raw_path

        return UsbDevice(
            instance_id=inst_id,
            name=f"USB Device ({vid}:{pid})" if vid and pid else "USB Device",
            hardware_ids=[f"USB\\VID_{vid}&PID_{pid}"] if vid and pid else [],
            vid=vid,
            pid=pid,
        )

    def _emit_snapshot_diff(self, current_devices: Dict[str, UsbDevice], now: datetime):
        new_ids = set(current_devices.keys()) - set(self._known_devices.keys())
        removed_ids = set(self._known_devices.keys()) - set(current_devices.keys())

        for nid in new_ids:
            dev = current_devices[nid]
            self._known_devices[nid] = dev
            self.device_connected.emit(UsbEvent(timestamp=now, event_type="CONNECTED", device=dev))

        for rid in removed_ids:
            dev = self._known_devices.pop(rid)
            dev.is_connected = False
            self.device_disconnected.emit(UsbEvent(timestamp=now, event_type="DISCONNECTED", device=dev))

    def stop(self):
        self._running = False
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_USER_STOP, 0, 0)
        self.wait(1500)
