"""Finds abnormal temperature readings.

Two simple rules, checked for every reading:
  1. LIMIT rule:  the temperature is above the safe limit for chilled food.
  2. JUMP rule:   the temperature is far from that unit's own recent "normal"
                  (the median of its previous readings).

The median is used instead of the average because a short spike barely moves
a median, so the unit's idea of "normal" stays accurate during a fault.

This is a statistical check, not a machine learning model. A possible upgrade
is to swap in an Isolation Forest (see README "Next steps").
"""
from statistics import median

SAFE_LIMIT_C = 8.0     # chilled food should stay below this
JUMP_C = 3.0           # how far from recent normal counts as abnormal
WINDOW = 12            # how many previous readings define "recent" (12 x 5 min = 1 hour)


def find_alerts(readings):
    """Return a list of alerts, oldest first.

    `readings` is the list produced by simulator.generate_readings().
    Each alert is the original reading plus a "reason" explaining why it was flagged.
    """
    alerts = []
    history = {}   # unit name -> list of that unit's earlier temperatures

    for reading in readings:
        unit, temp = reading["unit"], reading["temp_c"]
        earlier = history.setdefault(unit, [])
        recent = earlier[-WINDOW:]

        reasons = []
        if temp > SAFE_LIMIT_C:
            reasons.append(f"above safe limit of {SAFE_LIMIT_C}°C")
        # Only apply the jump rule once there is enough history to know what normal is.
        if len(recent) == WINDOW:
            normal = median(recent)
            if abs(temp - normal) > JUMP_C:
                reasons.append(f"{abs(temp - normal):.1f}°C away from recent normal of {normal:.1f}°C")

        if reasons:
            alerts.append({**reading, "reason": "; ".join(reasons)})
        earlier.append(temp)

    return alerts


def unit_status(readings, alerts):
    """Summarise each unit's latest reading, alert count, and current state."""
    latest_readings = {}

    for reading in readings:
        latest_readings[reading["unit"]] = reading

    alert_count = {}
    alerted_readings = set()

    for alert in alerts:
        unit = alert["unit"]
        alert_count[unit] = alert_count.get(unit, 0) + 1
        alerted_readings.add((unit, alert["timestamp"]))

    status = []

    for unit, reading in latest_readings.items():
        is_latest_alert = (
            unit,
            reading["timestamp"]
        ) in alerted_readings

        status.append({
            "unit": unit,
            "latest_temp_c": reading["temp_c"],
            "alert_count": alert_count.get(unit, 0),
            "state": "ALERT" if is_latest_alert else "OK"
        })

    return status
