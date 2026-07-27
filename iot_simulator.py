"""
iot_simulator.py
Simulates smart-meter / IoT sensor data for each device since we don't
have real hardware. Replace `read_sensor()` with real sensor / MQTT /
serial code when you connect actual ESP32 + ACS712 + ZMPT101B hardware.
"""

import random
import threading
import time
from datetime import datetime

import database

VOLTAGE_NOMINAL = 230.0  # Indian household voltage (V)


def _simulate_device_state(device):
    """
    Decide whether a device is ON/OFF right now and, if ON, how much
    power it's drawing (with realistic random fluctuation).
    Uses hour-of-day to bias certain devices (e.g. AC more likely at
    night, lights in evening) so the analytics look believable.
    """
    hour = datetime.now().hour
    name = device["name"]
    rated = device["rated_power_w"]

    # base probability device is ON
    prob_on = 0.5
    if "Air Conditioner" in name:
        prob_on = 0.75 if (hour >= 22 or hour <= 6) else 0.35
    elif "Refrigerator" in name:
        prob_on = 0.95  # almost always cycling
    elif "Tube Light" in name:
        prob_on = 0.85 if (hour >= 18 or hour <= 6) else 0.1
    elif "Fan" in name:
        prob_on = 0.7
    elif "Water Heater" in name:
        prob_on = 0.6 if (6 <= hour <= 9 or 18 <= hour <= 20) else 0.05
    elif "Washing Machine" in name:
        prob_on = 0.15
    elif "Television" in name:
        prob_on = 0.5 if (17 <= hour <= 23) else 0.1
    elif "Microwave" in name:
        prob_on = 0.2 if (7 <= hour <= 9 or 12 <= hour <= 14 or 19 <= hour <= 21) else 0.02

    is_on = random.random() < prob_on

    if not is_on:
        return 0.0, "OFF"

    # power fluctuates +/-15% around rated power, occasional spike (simulated fault)
    fluctuation = random.uniform(0.85, 1.15)
    power = rated * fluctuation

    # 2% chance of an abnormal spike -> useful for anomaly detection demo
    if random.random() < 0.02:
        power *= random.uniform(1.5, 2.2)

    return round(power, 2), "ON"


def generate_and_store_reading(device, interval_hours):
    power_w, status = _simulate_device_state(device)

    if status == "OFF":
        voltage, current, energy = 0.0, 0.0, 0.0
    else:
        voltage = round(random.uniform(215, 240), 1)
        current = round(power_w / voltage, 3)
        # Energy consumed during this interval (kWh) = power(kW) * time(h)
        energy = round((power_w / 1000.0) * interval_hours, 5)

    database.insert_reading(
        device_id=device["id"],
        voltage=voltage,
        current=current,
        power_w=power_w,
        energy_kwh=energy,
        status=status,
    )


class IoTSimulatorThread(threading.Thread):
    """
    Background thread that periodically generates a reading for every
    registered device, simulating a live IoT smart-metering network.
    """

    def __init__(self, poll_seconds=5):
        super().__init__(daemon=True)
        self.poll_seconds = poll_seconds
        self._stop_event = threading.Event()
        # interval expressed in hours (used for energy_kwh calculation)
        self.interval_hours = poll_seconds / 3600.0

    def run(self):
        while not self._stop_event.is_set():
            try:
                devices = database.get_devices()
                for device in devices:
                    generate_and_store_reading(device, self.interval_hours)
            except Exception as exc:
                print(f"[IoTSimulator] error: {exc}")
            time.sleep(self.poll_seconds)

    def stop(self):
        self._stop_event.set()


def start_simulator(poll_seconds=5):
    sim = IoTSimulatorThread(poll_seconds=poll_seconds)
    sim.start()
    return sim
