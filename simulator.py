"""Simulates temperature readings from cold-storage units.

There are no real sensors. This module generates realistic-looking data:
each unit hovers around its normal temperature with small random variation,
and a few "faults" (for example a door left open) are injected on purpose
so the detector has something to find.
"""
import random
from datetime import datetime, timedelta, timezone

# The storage units being "monitored" and their normal temperature in Celsius.
UNITS = {
    "Cooler A": 4.0,
    "Cooler B": 4.0,
    "Cooler C": 3.5,
    "Cooler D": 4.5,
}

INTERVAL_MINUTES = 5      # one reading every 5 minutes
HOURS = 24                # one day of history
NOISE = 0.3               # normal random variation, in degrees

# Injected faults: (unit, reading number where it starts, how many readings, temperature)
# 4 readings = 20 minutes. Edit this list to try different scenarios.
FAULTS = [
    ("Cooler A", 60, 4, 12.0),    # e.g. door left open
    ("Cooler C", 150, 4, 10.5),   # e.g. compressor trips
    ("Cooler D", 230, 4, 13.0),   # e.g. power dip
]


def generate_readings(faults=FAULTS, seed=42, end_time=None):
    """Return a list of readings, oldest first.

    Each reading is a dict: {"unit": str, "timestamp": ISO string, "temp_c": float}
    The seed makes the random numbers repeatable, so tests give the same result every run.
    """
    rng = random.Random(seed)
    end_time = end_time or datetime.now(timezone.utc).replace(second=0, microsecond=0)
    count = HOURS * 60 // INTERVAL_MINUTES          # 288 readings per unit
    start_time = end_time - timedelta(minutes=INTERVAL_MINUTES * (count - 1))

    readings = []
    for unit, normal_temp in UNITS.items():
        for i in range(count):
            temp = rng.gauss(normal_temp, NOISE)
            # If this reading falls inside a fault window, override the temperature.
            for fault_unit, fault_start, fault_length, fault_temp in faults:
                if unit == fault_unit and fault_start <= i < fault_start + fault_length:
                    temp = rng.gauss(fault_temp, NOISE)
            readings.append({
                "unit": unit,
                "timestamp": (start_time + timedelta(minutes=INTERVAL_MINUTES * i)).isoformat(),
                "temp_c": round(temp, 2),
            })
    return readings
