#!/usr/bin/env python3
"""xminer-api FastAPI сервер з веб-інтерфейсом.

Запуск:
    python main.py
    python main.py --config config.json
    python main.py --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from xminer_client import XMinerClient, XMinerError

# ── Config ─────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "miner_host": "192.168.1.147",
    "miner_port": 80,
    "miner_password": "admin",
    "miner_api_key": None,
    "server_host": "0.0.0.0",
    "server_port": 8000,
}


def load_config(path: str) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    return config


# ── Miner client singleton ─────────────────────────────────

_client: Optional[XMinerClient] = None
_client_lock = threading.Lock()


def get_client() -> XMinerClient:
    global _client
    with _client_lock:
        if _client is None:
            raise HTTPException(status_code=500, detail="Miner client not initialized")
        return _client


def init_client(config: dict[str, Any]) -> XMinerClient:
    global _client
    client = XMinerClient(
        host=config["miner_host"],
        port=config.get("miner_port", 80),
        api_key=config.get("miner_api_key"),
    )
    if config.get("miner_password"):
        try:
            client.unlock(config["miner_password"])
        except XMinerError:
            pass
    _client = client
    return client


# ── FastAPI app ────────────────────────────────────────────

app = FastAPI(title="xminer-api Web UI", version="1.0.0")


# ── API routes ─────────────────────────────────────────────

@app.get("/api/info")
def api_info():
    try:
        return get_client().get_info().__dict__
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/model")
def api_model():
    try:
        return get_client().get_model().__dict__
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/status")
def api_status():
    try:
        return get_client().get_status().__dict__
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/summary")
def api_summary():
    try:
        summary = get_client().get_summary()
        if summary.miner is None:
            return {"miner": None}
        m = summary.miner
        return {
            "miner": {
                "miner_state": m.miner_status.miner_state if m.miner_status else None,
                "throttled": m.miner_status.throttled if m.miner_status else None,
                "miner_type": m.miner_type,
                "hr_realtime": m.hr_realtime,
                "hr_average": m.hr_average,
                "hr_nominal": m.hr_nominal,
                "power_consumption": m.power_consumption,
                "power_efficiency": m.power_efficiency,
                "hw_errors": m.hw_errors,
                "hw_errors_percent": m.hw_errors_percent,
                "restart_count": m.restart_count,
                "chip_temp": {"min": m.chip_temp.min, "max": m.chip_temp.max} if m.chip_temp else None,
                "pcb_temp": {"min": m.pcb_temp.min, "max": m.pcb_temp.max} if m.pcb_temp else None,
                "cooling": {
                    "fan_duty": m.cooling.fan_duty,
                    "fans": [{"id": f.id, "rpm": f.rpm, "status": f.status} for f in m.cooling.fans],
                } if m.cooling else None,
                "pools": [
                    {
                        "id": p.id, "url": p.url, "user": p.user,
                        "status": p.status, "accepted": p.accepted,
                        "rejected": p.rejected, "stale": p.stale,
                    }
                    for p in m.pools
                ],
            }
        }
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/presets")
def api_presets():
    try:
        presets = get_client().get_autotune_presets()
        return [{"name": p.name, "pretty": p.pretty, "status": p.status, "modded_psu_required": p.modded_psu_required} for p in presets]
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/settings")
def api_settings():
    try:
        return get_client().get_settings()
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/metrics")
def api_metrics(time_slice: int = 3600, step: int = 300):
    try:
        return get_client().get_metrics(time_slice=time_slice, step=step)
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/mining/{action}")
def api_mining_action(action: str):
    client = get_client()
    actions = {
        "start": client.mining_start,
        "stop": client.mining_stop,
        "restart": client.mining_restart,
        "resume": client.mining_resume,
        "pause": client.mining_pause,
    }
    if action not in actions:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    try:
        actions[action]()
        return {"success": True, "action": action}
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/throttle/{percent}")
def api_throttle(percent: int):
    try:
        get_client().mining_throttle(percent)
        return {"success": True, "percent": percent}
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/preset/{name}")
def api_set_preset(name: str):
    try:
        result = get_client().save_settings({"miner": {"overclock": {"preset": name}}})
        return {"success": True, "preset": name, "restart_required": result.restart_required, "reboot_required": result.reboot_required}
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/switch-pool/{pool_id}")
def api_switch_pool(pool_id: int):
    try:
        get_client().mining_switch_pool(pool_id)
        return {"success": True, "pool_id": pool_id}
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.post("/api/reboot")
def api_reboot():
    try:
        result = get_client().system_reboot()
        return {"success": True, "reboot_after": result.after}
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/logs/{log_type}")
def api_logs(log_type: str):
    try:
        logs = get_client().get_logs(log_type)
        return {"logs": logs[-5000:] if len(logs) > 5000 else logs}
    except XMinerError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# ── Web UI ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


HTML_PAGE = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>xminer — Web UI</title>
<style>
  :root {
    --bg: #0f1117;
    --card: #1a1d27;
    --border: #2a2d3a;
    --text: #e4e6eb;
    --muted: #8b8e98;
    --accent: #f7931a;
    --accent-hover: #e88410;
    --green: #00c853;
    --red: #ff3d00;
    --yellow: #ffab00;
    --blue: #2196f3;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }
  .header {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .header h1 {
    font-size: 20px;
    font-weight: 600;
  }
  .header .logo {
    width: 32px; height: 32px;
    background: var(--accent);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: bold; color: #fff;
  }
  .header .status-badge {
    margin-left: auto;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
  }
  .status-badge.mining { background: rgba(0,200,83,0.15); color: var(--green); }
  .status-badge.stopped { background: rgba(255,61,0,0.15); color: var(--red); }
  .status-badge.other { background: rgba(255,171,0,0.15); color: var(--yellow); }
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  @media (max-width: 768px) { .container { grid-template-columns: 1fr; } }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }
  .card h2 {
    font-size: 15px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 16px;
  }
  .stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .stat {
    background: var(--bg);
    border-radius: 8px;
    padding: 14px;
  }
  .stat .label {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 4px;
  }
  .stat .value {
    font-size: 22px;
    font-weight: 700;
  }
  .stat .unit {
    font-size: 13px;
    color: var(--muted);
    font-weight: 400;
  }
  .btn-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .btn:active { transform: scale(0.97); }
  .btn-primary { background: var(--green); color: #fff; }
  .btn-primary:hover { background: #00b248; }
  .btn-danger { background: var(--red); color: #fff; }
  .btn-danger:hover { background: #e63600; }
  .btn-warning { background: var(--yellow); color: #000; }
  .btn-warning:hover { background: #e89e00; }
  .btn-secondary { background: var(--border); color: var(--text); }
  .btn-secondary:hover { background: #363949; }
  .btn-blue { background: var(--blue); color: #fff; }
  .btn-blue:hover { background: #1976d2; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .preset-select {
    width: 100%;
    padding: 10px 14px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 14px;
    margin-bottom: 12px;
  }
  .pool-list { display: flex; flex-direction: column; gap: 8px; }
  .pool-item {
    background: var(--bg);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .pool-item .pool-url { font-size: 13px; font-weight: 600; }
  .pool-item .pool-user { font-size: 12px; color: var(--muted); }
  .pool-item .pool-stats { margin-left: auto; font-size: 12px; color: var(--muted); }
  .pool-status {
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }
  .pool-status.active, .pool-status.working { background: rgba(0,200,83,0.15); color: var(--green); }
  .pool-status.offline, .pool-status.disabled { background: rgba(255,61,0,0.15); color: var(--red); }
  .fan-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .fan-item {
    background: var(--bg);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
  }
  .fan-item .fan-id { font-size: 11px; color: var(--muted); }
  .fan-item .fan-rpm { font-size: 18px; font-weight: 700; }
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 14px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    z-index: 1000;
    animation: slideIn 0.3s ease;
  }
  .toast.success { background: var(--green); color: #fff; }
  .toast.error { background: var(--red); color: #fff; }
  @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
  .full-width { grid-column: 1 / -1; }
  .log-box {
    background: var(--bg);
    border-radius: 8px;
    padding: 14px;
    font-family: 'Consolas', monospace;
    font-size: 12px;
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    color: var(--muted);
  }
  .refresh-btn {
    float: right;
    background: none;
    border: none;
    color: var(--muted);
    cursor: pointer;
    font-size: 14px;
  }
  .refresh-btn:hover { color: var(--text); }
</style>
</head>
<body>

<div class="header">
  <div class="logo">X</div>
  <h1 id="miner-name">xminer</h1>
  <span id="status-badge" class="status-badge other">—</span>
</div>

<div class="container">

  <!-- Stats -->
  <div class="card">
    <h2>Хешрейт та потужність</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="label">Realtime HR</div>
        <div class="value"><span id="hr-realtime">—</span> <span class="unit">GH/s</span></div>
      </div>
      <div class="stat">
        <div class="label">Average HR</div>
        <div class="value"><span id="hr-average">—</span> <span class="unit">GH/s</span></div>
      </div>
      <div class="stat">
        <div class="label">Nominal HR</div>
        <div class="value"><span id="hr-nominal">—</span> <span class="unit">GH/s</span></div>
      </div>
      <div class="stat">
        <div class="label">Power</div>
        <div class="value"><span id="power">—</span> <span class="unit">W</span></div>
      </div>
      <div class="stat">
        <div class="label">Efficiency</div>
        <div class="value"><span id="efficiency">—</span> <span class="unit">J/TH</span></div>
      </div>
      <div class="stat">
        <div class="label">HW Errors</div>
        <div class="value"><span id="hw-errors">—</span></div>
      </div>
    </div>
  </div>

  <!-- Temps & Fans -->
  <div class="card">
    <h2>Температури та охолодження</h2>
    <div class="stat-grid" style="margin-bottom:16px">
      <div class="stat">
        <div class="label">Chip Temp</div>
        <div class="value"><span id="chip-temp">—</span> <span class="unit">°C</span></div>
      </div>
      <div class="stat">
        <div class="label">PCB Temp</div>
        <div class="value"><span id="pcb-temp">—</span> <span class="unit">°C</span></div>
      </div>
      <div class="stat">
        <div class="label">Fan Duty</div>
        <div class="value"><span id="fan-duty">—</span> <span class="unit">%</span></div>
      </div>
      <div class="stat">
        <div class="label">Restarts</div>
        <div class="value"><span id="restarts">—</span></div>
      </div>
    </div>
    <div class="fan-grid" id="fan-grid"></div>
  </div>

  <!-- Mining Control -->
  <div class="card">
    <h2>Керування майнінгом</h2>
    <div class="btn-row" style="margin-bottom:16px">
      <button class="btn btn-primary" onclick="miningAction('start')">▶ Старт</button>
      <button class="btn btn-warning" onclick="miningAction('pause')">⏸ Пауза</button>
      <button class="btn btn-secondary" onclick="miningAction('resume')">▶ Resume</button>
      <button class="btn btn-secondary" onclick="miningAction('restart')">⟳ Restart</button>
      <button class="btn btn-danger" onclick="miningAction('stop')">⏹ Стоп</button>
    </div>
    <h2 style="margin-top:20px">Пресет автотюну</h2>
    <select class="preset-select" id="preset-select">
      <option value="">Завантаження...</option>
    </select>
    <button class="btn btn-blue" onclick="applyPreset()">Застосувати пресет</button>
  </div>

  <!-- Pools -->
  <div class="card">
    <h2>Пули</h2>
    <div class="pool-list" id="pool-list">
      <div style="color:var(--muted)">Завантаження...</div>
    </div>
  </div>

  <!-- System -->
  <div class="card full-width">
    <h2>Система <button class="refresh-btn" onclick="refresh()">↻ Оновити</button></h2>
    <div class="btn-row">
      <button class="btn btn-danger" onclick="rebootMiner()">⟳ Перезавантажити майнер</button>
      <button class="btn btn-secondary" onclick="loadLogs()">📄 Логи</button>
    </div>
    <div id="log-container" style="display:none;margin-top:16px">
      <div class="log-box" id="log-box">Завантаження...</div>
    </div>
  </div>

</div>

<script>
const api = (path, method = 'GET') =>
  fetch(path, { method }).then(r => r.ok ? r.json() : r.json().then(e => { throw new Error(e.detail || 'Error'); }));

function toast(msg, type = 'success') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

async function miningAction(action) {
  try {
    await api(`/api/mining/${action}`, 'POST');
    toast(`Mining: ${action} ✓`);
    setTimeout(refresh, 2000);
  } catch (e) { toast(e.message, 'error'); }
}

async function rebootMiner() {
  if (!confirm('Перезавантажити майнер?')) return;
  try {
    await api('/api/reboot', 'POST');
    toast('Rebooting... ✓');
  } catch (e) { toast(e.message, 'error'); }
}

async function applyPreset() {
  const sel = document.getElementById('preset-select');
  const preset = sel.value;
  if (!preset) return;
  try {
    const r = await api(`/api/preset/${preset}`, 'POST');
    toast(`Preset ${preset} applied ✓` + (r.restart_required ? ' (restart required)' : ''));
    setTimeout(refresh, 3000);
  } catch (e) { toast(e.message, 'error'); }
}

async function loadLogs() {
  const c = document.getElementById('log-container');
  c.style.display = 'block';
  const box = document.getElementById('log-box');
  box.textContent = 'Завантаження...';
  try {
    const r = await api('/api/logs/miner');
    box.textContent = r.logs || '(empty)';
    box.scrollTop = box.scrollHeight;
  } catch (e) { box.textContent = 'Error: ' + e.message; }
}

async function refresh() {
  try {
    const [info, status, summary, presets] = await Promise.all([
      api('/api/info'),
      api('/api/status'),
      api('/api/summary'),
      api('/api/presets'),
    ]);

    // Header
    document.getElementById('miner-name').textContent = info.miner || 'xminer';
    const badge = document.getElementById('status-badge');
    const state = status.miner_state;
    badge.textContent = state;
    badge.className = 'status-badge ' + (state === 'mining' ? 'mining' : state === 'stopped' ? 'stopped' : 'other');

    // Summary
    const m = summary.miner;
    if (m) {
      document.getElementById('hr-realtime').textContent = m.hr_realtime?.toFixed(0) || '—';
      document.getElementById('hr-average').textContent = m.hr_average?.toFixed(0) || '—';
      document.getElementById('hr-nominal').textContent = m.hr_nominal?.toFixed(0) || '—';
      document.getElementById('power').textContent = m.power_consumption || '—';
      document.getElementById('efficiency').textContent = m.power_efficiency?.toFixed(1) || '—';
      document.getElementById('hw-errors').textContent = `${m.hw_errors || 0} (${(m.hw_errors_percent || 0).toFixed(1)}%)`;
      document.getElementById('restarts').textContent = m.restart_count || 0;

      if (m.chip_temp) document.getElementById('chip-temp').textContent = `${m.chip_temp.min}-${m.chip_temp.max}`;
      if (m.pcb_temp) document.getElementById('pcb-temp').textContent = `${m.pcb_temp.min}-${m.pcb_temp.max}`;

      if (m.cooling) {
        document.getElementById('fan-duty').textContent = m.cooling.fan_duty;
        const fg = document.getElementById('fan-grid');
        fg.innerHTML = m.cooling.fans.map(f =>
          `<div class="fan-item"><div class="fan-id">Fan ${f.id}</div><div class="fan-rpm">${f.rpm}</div><div style="font-size:11px;color:${f.status==='ok'?'var(--green)':'var(--red)'}">${f.status}</div></div>`
        ).join('');
      }

      // Pools
      const pl = document.getElementById('pool-list');
      if (m.pools && m.pools.length) {
        pl.innerHTML = m.pools.map(p =>
          `<div class="pool-item">
            <span class="pool-status ${p.status}">${p.status}</span>
            <div>
              <div class="pool-url">${p.url}</div>
              <div class="pool-user">${p.user}</div>
            </div>
            <div class="pool-stats">A:${p.accepted} R:${p.rejected} S:${p.stale}</div>
          </div>`
        ).join('');
      } else {
        pl.innerHTML = '<div style="color:var(--muted)">No pools</div>';
      }
    }

    // Presets
    const sel = document.getElementById('preset-select');
    const currentPreset = sel.value;
    sel.innerHTML = presets.map(p =>
      `<option value="${p.name}">${p.pretty} — ${p.status}${p.modded_psu_required ? ' (modded PSU)' : ''}</option>`
    ).join('');
    if (currentPreset) sel.value = currentPreset;

  } catch (e) {
    toast('Refresh error: ' + e.message, 'error');
  }
}

refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""


# ── Main ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="xminer-api FastAPI server")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    parser.add_argument("--host", default=None, help="Server host (overrides config)")
    parser.add_argument("--port", type=int, default=None, help="Server port (overrides config)")
    args = parser.parse_args()

    config = load_config(args.config)

    host = args.host or config.get("server_host", "0.0.0.0")
    port = args.port or config.get("server_port", 8000)

    init_client(config)

    print(f"Starting xminer Web UI on http://{host}:{port}")
    print(f"Miner: {config['miner_host']}:{config.get('miner_port', 80)}")
    print(f"Config: {args.config}")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
