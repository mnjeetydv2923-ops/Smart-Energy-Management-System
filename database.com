"""
database.py
Handles all SQLite database operations for the
Smart Energy Monitoring System.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "smart_energy.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not already exist and seed devices."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            rated_power_w REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            voltage REAL NOT NULL,
            current REAL NOT NULL,
            power_w REAL NOT NULL,
            energy_kwh REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """)

    conn.commit()

    # Seed default devices only if table is empty
    cur.execute("SELECT COUNT(*) FROM devices")
    count = cur.fetchone()[0]
    if count == 0:
        default_devices = [
            ("Air Conditioner", "Cooling", 1500),
            ("Refrigerator", "Kitchen", 200),
            ("Washing Machine", "Laundry", 500),
            ("Ceiling Fan", "Cooling", 75),
            ("Tube Light", "Lighting", 40),
            ("Water Heater (Geyser)", "Heating", 2000),
            ("Television", "Entertainment", 120),
            ("Microwave Oven", "Kitchen", 1200),
        ]
        cur.executemany(
            "INSERT INTO devices (name, category, rated_power_w) VALUES (?, ?, ?)",
            default_devices,
        )
        conn.commit()

    conn.close()


def get_devices():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM devices").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_reading(device_id, voltage, current, power_w, energy_kwh, status):
    conn = get_connection()
    conn.execute(
        """INSERT INTO readings
           (device_id, timestamp, voltage, current, power_w, energy_kwh, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (device_id, datetime.now().isoformat(timespec="seconds"),
         voltage, current, power_w, energy_kwh, status),
    )
    conn.commit()
    conn.close()


def get_readings(device_id=None, hours=24, limit=5000):
    conn = get_connection()
    query = """
        SELECT r.*, d.name as device_name, d.category
        FROM readings r
        JOIN devices d ON r.device_id = d.id
        WHERE datetime(r.timestamp) >= datetime('now', ?)
    """
    params = [f"-{hours} hours"]
    if device_id:
        query += " AND r.device_id = ?"
        params.append(device_id)
    query += " ORDER BY r.timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_reading_per_device():
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.*, d.name as device_name, d.category, d.rated_power_w
        FROM readings r
        JOIN devices d ON r.device_id = d.id
        WHERE r.id IN (
            SELECT MAX(id) FROM readings GROUP BY device_id
        )
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
