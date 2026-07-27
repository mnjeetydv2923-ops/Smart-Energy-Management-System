"""
data_analysis.py
Pandas-based data analysis for the Smart Energy Monitoring System.
Computes consumption trends, device-wise contribution, peak demand
hours, estimated electricity cost, and simple anomaly detection.
"""

import pandas as pd
import database

# Electricity tariff (INR per kWh) - adjust to your local slab rate
TARIFF_PER_KWH = 7.5


def _readings_dataframe(hours=24):
    data = database.get_readings(hours=hours, limit=20000)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def get_summary(hours=24):
    """Overall totals: energy consumed, estimated cost, active devices."""
    df = _readings_dataframe(hours=hours)
    if df.empty:
        return {
            "total_energy_kwh": 0,
            "estimated_cost_inr": 0,
            "avg_power_w": 0,
            "active_devices": 0,
            "total_devices": len(database.get_devices()),
        }

    total_energy = df["energy_kwh"].sum()
    latest = database.get_latest_reading_per_device()
    active = sum(1 for r in latest if r["status"] == "ON")

    return {
        "total_energy_kwh": round(total_energy, 3),
        "estimated_cost_inr": round(total_energy * TARIFF_PER_KWH, 2),
        "avg_power_w": round(df[df["status"] == "ON"]["power_w"].mean() or 0, 2),
        "active_devices": active,
        "total_devices": len(database.get_devices()),
    }


def get_device_wise_consumption(hours=24):
    """Energy consumption grouped by device -> for pie/bar chart."""
    df = _readings_dataframe(hours=hours)
    if df.empty:
        return []

    grouped = (
        df.groupby("device_name")["energy_kwh"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    grouped["energy_kwh"] = grouped["energy_kwh"].round(4)
    grouped["cost_inr"] = (grouped["energy_kwh"] * TARIFF_PER_KWH).round(2)
    return grouped.to_dict(orient="records")


def get_hourly_trend(hours=24):
    """Total energy consumed per hour -> for line/area chart."""
    df = _readings_dataframe(hours=hours)
    if df.empty:
        return []

    df["hour"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:00")
    trend = df.groupby("hour")["energy_kwh"].sum().reset_index()
    trend["energy_kwh"] = trend["energy_kwh"].round(4)
    return trend.to_dict(orient="records")


def get_peak_hours(hours=24, top_n=3):
    """Identify the top-N hours with highest total power draw."""
    df = _readings_dataframe(hours=hours)
    if df.empty:
        return []

    df["hour_of_day"] = df["timestamp"].dt.hour
    peak = (
        df.groupby("hour_of_day")["power_w"]
        .mean()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    peak["power_w"] = peak["power_w"].round(2)
    return peak.to_dict(orient="records")


def detect_anomalies(hours=24, z_threshold=2.5):
    """
    Simple statistical anomaly detection: flag readings whose power
    draw deviates more than `z_threshold` standard deviations from
    that device's own mean (per-device z-score).
    """
    df = _readings_dataframe(hours=hours)
    if df.empty:
        return []

    on_df = df[df["status"] == "ON"].copy()
    if on_df.empty:
        return []

    stats = on_df.groupby("device_id")["power_w"].agg(["mean", "std"]).reset_index()
    on_df = on_df.merge(stats, on="device_id", suffixes=("", "_stat"))
    on_df["std"] = on_df["std"].fillna(0)
    on_df["z_score"] = on_df.apply(
        lambda row: 0 if row["std"] == 0 else (row["power_w"] - row["mean"]) / row["std"],
        axis=1,
    )

    anomalies = on_df[on_df["z_score"].abs() > z_threshold]
    anomalies = anomalies.sort_values("timestamp", ascending=False).head(20)

    return anomalies[[
        "device_name", "timestamp", "power_w", "mean", "z_score"
    ]].round(2).to_dict(orient="records")


def get_full_analytics(hours=24):
    """Bundle everything the dashboard needs in one call."""
    return {
        "summary": get_summary(hours=hours),
        "device_consumption": get_device_wise_consumption(hours=hours),
        "hourly_trend": get_hourly_trend(hours=hours),
        "peak_hours": get_peak_hours(hours=hours),
        "anomalies": detect_anomalies(hours=hours),
    }
