"""KimPulse - cold storage monitoring (web app).

Routes:
  /               the dashboard page
  /health         used by the deploy pipeline and the Azure Monitor alert
  /api/readings   all simulated readings as JSON
  /api/alerts     abnormal readings as JSON
  /api/status     one summary row per storage unit

Run locally:   flask --app app run     (then open http://localhost:5000)
"""
from flask import Flask, jsonify, render_template

from detector import SAFE_LIMIT_C, find_alerts, unit_status
from simulator import generate_readings

app = Flask(__name__)

# The data is generated once when the app starts. There is no database:
# everything is simulated, so there is nothing to store.
READINGS = generate_readings()
ALERTS = find_alerts(READINGS)


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/api/readings")
def api_readings():
    return jsonify(READINGS)


@app.route("/api/alerts")
def api_alerts():
    return jsonify(ALERTS)


@app.route("/api/status")
def api_status():
    return jsonify(unit_status(READINGS, ALERTS))


@app.route("/")
def dashboard():
    return render_template(
        "index.html",
        units=unit_status(READINGS, ALERTS),
        alerts=list(reversed(ALERTS)),   # newest first for the table
        safe_limit=SAFE_LIMIT_C,
    )


if __name__ == "__main__":
    app.run(debug=True)
