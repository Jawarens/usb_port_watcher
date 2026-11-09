import json
from datetime import datetime
from device_model import UsbDevice, UsbEvent
from export_utils import (
    export_events_to_csv,
    export_events_to_json,
    generate_device_diagnostic_text,
)
from win32_usb import enumerate_usb_devices


def test_vid_pid_extraction():
    dev = UsbDevice(
        instance_id=r"USB\VID_0403&PID_6001\A50285BI",
        name="FT232R USB UART",
        hardware_ids=[r"USB\VID_0403&PID_6001&REV_0600"],
        problem_code=0,
    )
    assert dev.vid == "0403"
    assert dev.pid == "6001"
    assert dev.vid_pid_str == "0403:6001"
    assert dev.is_healthy is True
    assert dev.problem_description[0] == "Normal"


def test_problem_codes():
    dev_missing = UsbDevice(
        instance_id=r"USB\VID_1234&PID_5678\0001",
        name="Unknown USB Device",
        problem_code=28,
    )
    assert dev_missing.is_healthy is False
    assert dev_missing.problem_description[0] == "Missing Driver"

    dev_code43 = UsbDevice(
        instance_id=r"USB\VID_0000&PID_0002\5&123456",
        name="Descriptor Request Failed",
        problem_code=43,
    )
    assert dev_code43.is_healthy is False
    assert "Code 43" in dev_code43.problem_description[1]


def test_exports_and_diagnostic_report(tmp_path):
    dev = UsbDevice(
        instance_id=r"USB\VID_0403&PID_6001\A50285BI",
        name="FT232R USB UART",
        manufacturer="FTDI",
        hardware_ids=[r"USB\VID_0403&PID_6001&REV_0600"],
        location="Port_#0001.Hub_#0004",
        problem_code=0,
        driver_provider="FTDI",
        driver_version="2.12.36.4",
    )
    evt = UsbEvent(
        timestamp=datetime(2026, 11, 9, 19, 30, 0),
        event_type="CONNECTED",
        device=dev,
    )

    csv_file = tmp_path / "events.csv"
    json_file = tmp_path / "events.json"

    export_events_to_csv(str(csv_file), [evt])
    export_events_to_json(str(json_file), [evt])

    assert csv_file.exists()
    csv_text = csv_file.read_text(encoding="utf-8")
    assert "0403:6001" in csv_text
    assert "FT232R USB UART" in csv_text

    assert json_file.exists()
    json_data = json.loads(json_file.read_text(encoding="utf-8"))
    assert len(json_data) == 1
    assert json_data[0]["device"]["vid_pid"] == "0403:6001"

    report = generate_device_diagnostic_text(dev)
    assert "USB DEVICE DIAGNOSTIC REPORT" in report
    assert "0403:6001" in report
    assert "HEALTHY / OPERATING NORMALLY" in report


def test_win32_enumerate_usb_devices():
    devices = enumerate_usb_devices()
    assert isinstance(devices, dict)
    for key, dev in devices.items():
        assert isinstance(key, str)
        assert isinstance(dev, UsbDevice)
        assert dev.instance_id != ""

