"""
app.py
Main Flask application for the Smart Energy Monitoring System (IoT + Data Analysis).

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, jsonify, request, send_from_directory

import database
import data_analysis
from iot_simulator import start_simulator

app = Flask(__name__, static_folder="static", static_url_path="")

# ---------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------------------------------------------------------------------
# API: Devices
# ---------------------------------------------------------------------
@app.route("/api/devices")
def api_devices():
    return jsonify(database.get_devices())


@app.route("/api/devices/live")
def api_devices_live():
    """Latest reading per device -> used for the live status cards."""
    return jsonify(database.get_latest_reading_per_device())


# ---------------------------------------------------------------------
# API: Raw readings
# ---------------------------------------------------------------------
@app.route("/api/readings")
def api_readings():
    device_id = request.args.get("device_id", type=int)
    hours = request.args.get("hours", default=24, type=int)
    return jsonify(database.get_readings(device_id=device_id, hours=hours))


# ---------------------------------------------------------------------
# API: Data analysis / analytics
# ---------------------------------------------------------------------
@app.route("/api/summary")
def api_summary():
    hours = request.args.get("hours", default=24, type=int)
    return jsonify(data_analysis.get_summary(hours=hours))


@app.route("/api/analytics")
def api_analytics():
    hours = request.args.get("hours", default=24, type=int)
    return jsonify(data_analysis.get_full_analytics(hours=hours))


@app.route("/api/analytics/device-consumption")
def api_device_consumption():
    hours = request.args.get("hours", default=24, type=int)
    return jsonify(data_analysis.get_device_wise_consumption(hours=hours))


@app.route("/api/analytics/hourly-trend")
def api_hourly_trend():
    hours = request.args.get("hours", default=24, type=int)
    return jsonify(data_analysis.get_hourly_trend(hours=hours))


@app.route("/api/analytics/peak-hours")
def api_peak_hours():
    hours = request.args.get("hours", default=24, type=int)
    return jsonify(data_analysis.get_peak_hours(hours=hours))


@app.route("/api/analytics/anomalies")
def api_anomalies():
    hours = request.args.get("hours", default=24, type=int)
    return jsonify(data_analysis.detect_anomalies(hours=hours))


# ---------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------
def bootstrap():
    database.init_db()
    # Background thread simulates IoT smart-meter readings every 5 seconds.
    # Swap this out for real MQTT / serial sensor ingestion in production.
    start_simulator(poll_seconds=5)


bootstrap()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
