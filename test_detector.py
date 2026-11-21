"""Tests for the anomaly check. Run from the backend/ folder with:  python -m pytest"""
from detector import find_alerts
from simulator import FAULTS, INTERVAL_MINUTES, generate_readings


def test_normal_readings_raise_no_alerts():
    readings = generate_readings(faults=[])
    assert find_alerts(readings) == []


def test_every_injected_fault_is_detected():
    alerts = find_alerts(generate_readings())
    for unit, _start, _length, _temp in FAULTS:
        assert any(a["unit"] == unit for a in alerts), f"fault in {unit} was missed"


def test_alerts_only_happen_during_faults():
    readings = generate_readings()
    # Work out which (unit, timestamp) pairs fall inside an injected fault.
    by_unit = {}
    for r in readings:
        by_unit.setdefault(r["unit"], []).append(r["timestamp"])
    expected = {(unit, by_unit[unit][i])
                for unit, start, length, _temp in FAULTS
                for i in range(start, start + length)}
    flagged = {(a["unit"], a["timestamp"]) for a in find_alerts(readings)}
    assert flagged == expected


def test_reading_interval_is_five_minutes():
    assert INTERVAL_MINUTES == 5
