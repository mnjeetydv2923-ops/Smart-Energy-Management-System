# Smart Energy Monitoring System using IoT and Data Analysis

A full-stack BTech project that simulates a smart-meter IoT network,
stores readings in a database, analyzes consumption with **pandas**,
and displays everything on a live, auto-refreshing web dashboard.

## Tech Stack
- **Backend:** Python, Flask (REST API)
- **Database:** SQLite
- **Data Analysis:** pandas / numpy
- **IoT Layer:** Simulated smart-meter sensor readings (background thread) — designed to be swapped for real ESP32 / ACS712 (current sensor) / ZMPT101B (voltage sensor) hardware over MQTT or Serial
- **Frontend:** HTML, CSS, JavaScript, Chart.js (no framework needed)

## Features
- Live dashboard: total energy (kWh), estimated electricity cost, average
  active power, active device count
- Device-wise energy consumption (doughnut chart)
- Hourly consumption trend (line chart)
- Peak demand hour detection (bar chart)
- Statistical anomaly detection (z-score based) — flags abnormal power spikes,
  e.g. a faulty appliance drawing more current than usual
- Live per-device status cards (ON/OFF, voltage, current, power)
- Selectable time range: 1 hr / 6 hr / 24 hr / 7 days

## Project Structure
```
smart_energy_monitoring/
├── app.py              # Flask app + REST API routes
├── database.py         # SQLite schema + queries
├── iot_simulator.py    # Simulated IoT sensor data generator (background thread)
├── data_analysis.py    # pandas-based analytics (trends, cost, anomalies)
├── requirements.txt
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/script.js
└── README.md
```

## Setup & Run

1. Install Python 3.9+ then install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python app.py
   ```

3. Open your browser at:
   ```
   http://127.0.0.1:5000
   ```

The app auto-creates `smart_energy.db` on first run, seeds 8 sample
devices (AC, Fridge, Washing Machine, Fan, Tube Light, Geyser, TV,
Microwave), and starts generating a simulated reading for every device
every 5 seconds. The dashboard auto-refreshes every 5 seconds too, so
you'll see live data building up immediately.

## How the "IoT" part works
`iot_simulator.py` runs in a background thread and generates realistic
readings (voltage, current, power, energy) for each device, with
probabilities biased by time of day (e.g. AC more likely at night,
lights more likely in the evening) and an occasional random power spike
to demonstrate anomaly detection. This mimics a network of smart plugs
reporting into a hub.

**To connect real hardware:** replace `_simulate_device_state()` in
`iot_simulator.py` with code that reads from your actual sensors (e.g.
an ESP32 publishing JSON over MQTT, or reading a serial port from an
Arduino + ACS712 current sensor + ZMPT101B voltage sensor). Everything
downstream (database, analysis, dashboard) works unchanged, since it
only cares about the `(voltage, current, power_w, energy_kwh, status)`
tuple.

## How the data analysis part works
`data_analysis.py` uses `pandas` to:
- Group readings by device and time to compute consumption trends
- Estimate electricity cost using a configurable tariff (`TARIFF_PER_KWH`
  in INR/kWh — change this to your local electricity board's rate)
- Compute per-device mean and standard deviation of power draw, then
  flag any reading with a z-score beyond ±2.5 as an anomaly (useful for
  detecting faulty appliances or electricity theft/leakage)

## Ideas for extending this project (for your report / viva)
- Swap SQLite for InfluxDB/TimescaleDB for true time-series storage at scale
- Add user authentication and multi-household support
- Add ML-based load forecasting (e.g. Prophet or LSTM) instead of z-score anomaly detection
- Push alerts via email/SMS/Telegram when anomalies are detected
- Deploy backend on Raspberry Pi as a home energy-monitoring hub
- Add a mobile app (Flutter/React Native) consuming the same REST API
