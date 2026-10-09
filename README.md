# USB Port Watcher 🔌

A lightweight, real-time Windows desktop application for monitoring USB ports, connection/disconnection events, port states, hardware IDs (VID/PID), and driver diagnostics.

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![GUI](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![OS](https://img.shields.io/badge/Platform-Windows_10_|_11-0078D6.svg)

<p align="center">
  <a href="https://ko-fi.com/F0T028FQJQ">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="ko-fi" />
  </a>
</p>

---

## ✨ Key Features

1. **⚡ Microsecond PnP Event Detection**:
   - Hooks native Windows `WM_DEVICECHANGE` (`DBT_DEVICEARRIVAL` & `DBT_DEVICEREMOVECOMPLETE`) messages via a dedicated background message pump.
   - Instantly logs when any device is plugged in or unplugged.

2. **📋 Live Event Stream & Filtering**:
   - Color-coded badges for **🟢 CONNECTED**, **🔴 DISCONNECTED**, and **⚠️ DRIVER CHANGED**.
   - Real-time search filter by Device Name, `VID:PID`, Port/Hub location, or Driver.
   - Filter modes: *All Events*, *Connected*, *Disconnected*, and *⚠️ Driver Issues Only*.

3. **🔍 Deep Device Inspector & Machine ID**:
   - **Device Instance ID / Machine Path**: Complete PnP device tree path (e.g. `USB\VID_0403&PID_6001\A50285BI`).
   - **Hardware IDs & Compatible IDs**: Clean list of all matching hardware identifiers.
   - **Port & Hub Location**: Exact hub and port index (e.g. `Port_#0001.Hub_#0004`).
   - **Driver Details**: Driver Provider, Version, Date, Service, and Matching INF.

4. **⚠️ Driver Health & Problem Code Diagnostics**:
   - Evaluates Windows Configuration Manager status (`CM_Get_DevNode_Status`):
     - **Code 0**: Healthy / Operating Normally.
     - **Code 28**: Missing Driver (*Drivers for this device are not installed*).
     - **Code 10**: Failed to Start (*Device cannot start*).
     - **Code 43**: Hardware / Post Error (*Windows stopped this device because it reported problems*).
     - **Code 22**: Disabled.
   - Prominent alert boxes explaining the problem and next recovery steps.

5. **🎯 1-Click Driver Hunting**:
   - 📋 **1-Click Copy**: VID:PID (`0403:6001`), Hardware ID, or Device Instance ID.
   - 🌐 **DeviceHunt USB DB**: Instant lookup in the community USB ID database.
   - 🌐 **Microsoft Update Catalog**: Direct search for official Windows driver packages.
   - 🔍 **Google Driver Search**: Targeted web search using the exact hardware identifier.
   - ⚙️ **Windows Device Manager**: Quick-launch shortcut to `devmgmt.msc`.
   - 📋 **Copy Full Diagnostic Report**: Formatted plain-text summary ready for support tickets or forum troubleshooting.

6. **💾 Export & Logging**:
   - Export event history to structured **CSV** or **JSON**.
   - Pause / resume live logging at any time.

---

## 🚀 Quick Start

### Option A: One-Click Launch
Double-click [`run.bat`](file:///c:/Users/Jawarens/Documents/GitHub/usb_port_watcher/run.bat).

### Option B: Terminal Launch
```powershell
cd c:\Users\Jawarens\Documents\GitHub\usb_port_watcher
.\.venv\Scripts\python.exe main.py
```

---

## 🛠️ Project Structure

```
usb_port_watcher/
├── main.py              # Application entry point
├── run.bat              # One-click Windows launcher
├── requirements.txt     # Python dependencies (PyQt6)
├── styles.py            # Modern dark slate/cyan QSS theme
├── device_model.py      # UsbDevice, UsbEvent, and Windows CM problem codes
├── win32_usb.py         # Win32 SetupAPI, CfgMgr32, and WM_DEVICECHANGE listener
├── export_utils.py      # CSV, JSON, and Diagnostic report generation
└── ui/
    ├── __init__.py
    ├── widgets.py       # Badges, Copy buttons, Stat cards, Filter bar
    ├── inspector_panel.py # Deep device inspector & driver helper panel
    └── main_window.py   # Main window with tabs, event table, and toolbar
```

---

## ☕ Support the Project

If this project saves you time or helps you troubleshoot USB hardware issues, please consider supporting development!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/F0T028FQJQ)
