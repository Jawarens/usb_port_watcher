import csv
import json
from datetime import datetime
from typing import List
from device_model import UsbDevice, UsbEvent

def export_events_to_csv(filepath: str, events: List[UsbEvent]):
    """Export a list of USB events to a CSV file."""
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "Event Type",
            "Device Name",
            "VID:PID",
            "Problem Code",
            "Status",
            "Location",
            "Manufacturer",
            "Device Instance ID",
            "Hardware IDs",
            "Driver Provider",
            "Driver Version",
            "Driver Date",
        ])
        for evt in events:
            dev = evt.device
            writer.writerow([
                evt.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                evt.event_type,
                dev.name,
                dev.vid_pid_str,
                f"Code {dev.problem_code}" if dev.problem_code != 0 else "Normal (0)",
                dev.problem_description[0],
                dev.location,
                dev.manufacturer,
                dev.instance_id,
                "; ".join(dev.hardware_ids),
                dev.driver_provider,
                dev.driver_version,
                dev.driver_date,
            ])

def export_events_to_json(filepath: str, events: List[UsbEvent]):
    """Export a list of USB events to a JSON file."""
    data = []
    for evt in events:
        dev = evt.device
        data.append({
            "timestamp": evt.timestamp.isoformat(),
            "event_type": evt.event_type,
            "device": {
                "name": dev.name,
                "description": dev.description,
                "vid": dev.vid,
                "pid": dev.pid,
                "vid_pid": dev.vid_pid_str,
                "instance_id": dev.instance_id,
                "hardware_ids": dev.hardware_ids,
                "compatible_ids": dev.compatible_ids,
                "manufacturer": dev.manufacturer,
                "device_class": dev.device_class,
                "service": dev.service,
                "location": dev.location,
                "problem_code": dev.problem_code,
                "problem_name": dev.problem_description[0],
                "problem_detail": dev.problem_description[1],
                "driver_provider": dev.driver_provider,
                "driver_version": dev.driver_version,
                "driver_date": dev.driver_date,
                "matching_device_id": dev.matching_device_id,
                "is_connected": dev.is_connected,
            },
            "raw_path": evt.raw_path,
        })
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_device_diagnostic_text(dev: UsbDevice) -> str:
    """Generate a clean text report for a single USB device, ideal for tech support / forum posts / driver searches."""
    status_title, status_desc = dev.problem_description
    health_str = "HEALTHY / OPERATING NORMALLY" if dev.is_healthy else f"PROBLEM DETECTED: {status_title} (Code {dev.problem_code})"
    
    hwids_str = "\n".join([f"    - {hid}" for hid in dev.hardware_ids]) or "    None listed"
    compids_str = "\n".join([f"    - {cid}" for cid in dev.compatible_ids]) or "    None listed"

    report = f"""==================================================
USB DEVICE DIAGNOSTIC REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
==================================================
Device Name       : {dev.name}
Description       : {dev.description or 'N/A'}
Manufacturer      : {dev.manufacturer or 'N/A'}
Device Class      : {dev.device_class or 'N/A'}
Connected State   : {'Connected' if dev.is_connected else 'Disconnected'}

[IDENTIFIERS & DRIVER MATCHING]
Vendor ID (VID)   : {dev.vid or 'N/A'}
Product ID (PID)  : {dev.pid or 'N/A'}
VID:PID           : {dev.vid_pid_str}
Device Instance ID: {dev.instance_id}
Location / Port   : {dev.location or 'N/A'}

Hardware IDs:
{hwids_str}

Compatible IDs:
{compids_str}

[DRIVER STATUS & HEALTH]
Overall Health    : {health_str}
Problem Code      : {dev.problem_code}
Problem Summary   : {status_desc}
Driver Provider   : {dev.driver_provider or 'No driver loaded / Missing'}
Driver Version    : {dev.driver_version or 'N/A'}
Driver Date       : {dev.driver_date or 'N/A'}
Service Name      : {dev.service or 'N/A'}
Matching INF ID   : {dev.matching_device_id or 'N/A'}

[DRIVER SEARCH ASSISTANCE]
Lookup URLs:
  - DeviceHunt USB : https://devicehunt.com/search/type/usb/vendor/{dev.vid or ''}/device/{dev.pid or ''}
  - MS Update Cat  : https://www.catalog.update.microsoft.com/Search.aspx?q={dev.vid_pid_str}
  - Google Search  : https://www.google.com/search?q={dev.primary_hardware_id.replace(' ', '+')}+driver
=================================================="""
    return report
