const API = {
  summary: (h) => `/api/summary?hours=${h}`,
  analytics: (h) => `/api/analytics?hours=${h}`,
  devicesLive: `/api/devices/live`,
};

let trendChart, deviceChart, peakChart;
const hoursSelect = document.getElementById("hoursRange");

function getHours() {
  return hoursSelect.value;
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return res.json();
}

function formatNumber(n, decimals = 2) {
  if (n === null || n === undefined || isNaN(n)) return "--";
  return Number(n).toFixed(decimals);
}

// ---------------------------------------------------------------
// Summary cards
// ---------------------------------------------------------------
function updateSummaryCards(summary) {
  document.getElementById("totalEnergy").textContent = `${formatNumber(summary.total_energy_kwh, 3)} kWh`;
  document.getElementById("totalCost").textContent = `₹${formatNumber(summary.estimated_cost_inr)}`;
  document.getElementById("avgPower").textContent = `${formatNumber(summary.avg_power_w)} W`;
  document.getElementById("activeDevices").textContent = `${summary.active_devices} / ${summary.total_devices}`;
}

// ---------------------------------------------------------------
// Trend line chart
// ---------------------------------------------------------------
function renderTrendChart(hourlyTrend) {
  const ctx = document.getElementById("trendChart");
  const labels = hourlyTrend.map(d => d.hour.slice(5)); // trim year
  const data = hourlyTrend.map(d => d.energy_kwh);

  if (trendChart) {
    trendChart.data.labels = labels;
    trendChart.data.datasets[0].data = data;
    trendChart.update();
    return;
  }

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Energy (kWh)",
        data,
        borderColor: "#22d3ee",
        backgroundColor: "rgba(34, 211, 238, 0.15)",
        tension: 0.35,
        fill: true,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#e2e8f0" } } },
      scales: {
        x: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
        y: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
      },
    },
  });
}

// ---------------------------------------------------------------
// Device-wise pie chart
// ---------------------------------------------------------------
const PIE_COLORS = ["#22d3ee", "#34d399", "#fbbf24", "#f87171", "#a78bfa", "#f472b6", "#60a5fa", "#facc15"];

function renderDeviceChart(deviceConsumption) {
  const ctx = document.getElementById("deviceChart");
  const labels = deviceConsumption.map(d => d.device_name);
  const data = deviceConsumption.map(d => d.energy_kwh);

  if (deviceChart) {
    deviceChart.data.labels = labels;
    deviceChart.data.datasets[0].data = data;
    deviceChart.update();
    return;
  }

  deviceChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: PIE_COLORS }],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom", labels: { color: "#e2e8f0", boxWidth: 12 } } },
    },
  });
}

// ---------------------------------------------------------------
// Peak hours bar chart
// ---------------------------------------------------------------
function renderPeakChart(peakHours) {
  const ctx = document.getElementById("peakChart");
  const labels = peakHours.map(d => `${d.hour_of_day}:00`);
  const data = peakHours.map(d => d.power_w);

  if (peakChart) {
    peakChart.data.labels = labels;
    peakChart.data.datasets[0].data = data;
    peakChart.update();
    return;
  }

  peakChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Avg Power (W)", data, backgroundColor: "#34d399" }],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#e2e8f0" } } },
      scales: {
        x: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
        y: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
      },
    },
  });
}

// ---------------------------------------------------------------
// Anomalies list
// ---------------------------------------------------------------
function renderAnomalies(anomalies) {
  const container = document.getElementById("anomalyList");
  if (!anomalies || anomalies.length === 0) {
    container.innerHTML = `<p class="empty-state">No anomalies detected yet.</p>`;
    return;
  }

  container.innerHTML = anomalies.map(a => `
    <div class="anomaly-item">
      <div class="title">${a.device_name} - unusual power draw</div>
      <div class="details">
        ${a.power_w} W recorded (avg ${a.mean} W, z-score ${a.z_score}) at ${a.timestamp}
      </div>
    </div>
  `).join("");
}

// ---------------------------------------------------------------
// Live device grid
// ---------------------------------------------------------------
function renderDeviceGrid(liveDevices) {
  const grid = document.getElementById("deviceGrid");
  if (!liveDevices || liveDevices.length === 0) {
    grid.innerHTML = `<p class="empty-state">Waiting for first sensor readings...</p>`;
    return;
  }

  grid.innerHTML = liveDevices.map(d => `
    <div class="device-card">
      <p class="name">${d.device_name}</p>
      <span class="status ${d.status}">${d.status}</span>
      <p class="metric">Power: ${formatNumber(d.power_w)} W</p>
      <p class="metric">Voltage: ${formatNumber(d.voltage, 1)} V</p>
      <p class="metric">Current: ${formatNumber(d.current, 3)} A</p>
      <p class="metric">Rated: ${d.rated_power_w} W</p>
    </div>
  `).join("");
}

// ---------------------------------------------------------------
// Main refresh loop
// ---------------------------------------------------------------
async function refreshDashboard() {
  const hours = getHours();
  try {
    const [analytics, liveDevices] = await Promise.all([
      fetchJSON(API.analytics(hours)),
      fetchJSON(API.devicesLive),
    ]);

    updateSummaryCards(analytics.summary);
    renderTrendChart(analytics.hourly_trend);
    renderDeviceChart(analytics.device_consumption);
    renderPeakChart(analytics.peak_hours);
    renderAnomalies(analytics.anomalies);
    renderDeviceGrid(liveDevices);
  } catch (err) {
    console.error("Dashboard refresh failed:", err);
  }
}

hoursSelect.addEventListener("change", refreshDashboard);

refreshDashboard();
setInterval(refreshDashboard, 5000);
