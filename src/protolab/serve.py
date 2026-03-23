"""Persistent HTTP server and web dashboard for protolab.

Wraps all existing business logic (store, config, check, analyze, resynthesis,
correct) behind a FastAPI JSON API and serves a self-contained HTML dashboard.

Usage::

    protolab serve              # start on default port 8080
    protolab serve --port 9090  # custom port
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

import protolab
from .analyze import analyze_corrections
from .check import evaluate_triggers
from .config import load_config
from .correct import extract_rule
from .resynthesis import assemble_prompt, promote_resynthesis, run_resynthesis, stage_resynthesis
from .store import load_corrections, load_rules, next_id, save_corrections, save_rules

logger = logging.getLogger(__name__)

DEFAULT_PORT = 8080
POLL_INTERVAL = 2.0
MAX_SSE_CONNECTIONS = 10


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CorrectionCreate(BaseModel):
    subject: str = Field(max_length=200)
    step: str = Field(max_length=200)
    protocol_output: str = Field(max_length=10_000)
    correct_output: str = Field(max_length=10_000)
    reasoning: str = Field(max_length=10_000)
    rule: str | None = Field(default=None, max_length=5_000)


class ConfigPatch(BaseModel):
    total_corrections: int | None = Field(default=None, ge=1, le=10_000)
    cluster_threshold: float | None = Field(default=None, ge=0.01, le=1.0)
    preventable_errors: int | None = Field(default=None, ge=1, le=10_000)
    max_days_since_resynthesis: int | None = Field(default=None, ge=1, le=3650)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(obj: dict) -> dict:
    """Make a Correction or Rule dict JSON-serializable."""
    result = dict(obj)
    for key, val in result.items():
        if isinstance(val, datetime):
            result[key] = val.isoformat()
    return result


def _mtime(path: Path) -> float:
    """Return mtime of a path, or 0.0 if it doesn't exist."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _protocol_info(config) -> dict:
    """Build protocol metadata dict."""
    proto_path = config.root / config.protocol_path
    try:
        mtime = datetime.fromtimestamp(proto_path.stat().st_mtime, tz=timezone.utc)
        last_modified = mtime.isoformat()
    except OSError:
        last_modified = None
    return {
        "path": str(config.protocol_path),
        "version": config.protocol_version,
        "last_modified": last_modified,
    }


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(config_path: Path) -> FastAPI:
    """Create and return the FastAPI application.

    All route handlers re-read config from disk on each request so CLI
    and server never diverge.
    """
    # Validate config is loadable at startup
    load_config(config_path)

    app = FastAPI(title="Protolab", version=protolab.__version__)
    app.state.config_path = config_path

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _config() -> Any:
        return load_config(app.state.config_path)

    # -------------------------------------------------------------------
    # GET /api/status
    # -------------------------------------------------------------------
    @app.get("/api/status")
    def get_status():
        config = _config()
        corrections = load_corrections(config)
        rules = load_rules(config)
        analysis = analyze_corrections(corrections, rules)
        triggers = evaluate_triggers(config, corrections, rules)

        dates = [c.get("date") for c in corrections if c.get("date")]
        date_strs = []
        for d in dates:
            if isinstance(d, datetime):
                date_strs.append(d.isoformat())
            elif isinstance(d, str):
                date_strs.append(d)

        # Rules by confidence
        by_confidence: dict[str, int] = {}
        for r in rules:
            conf = r.get("confidence", "unknown")
            by_confidence[conf] = by_confidence.get(conf, 0) + 1

        return {
            "protocol": _protocol_info(config),
            "corrections": {
                "total": len(corrections),
                "oldest": min(date_strs) if date_strs else None,
                "newest": max(date_strs) if date_strs else None,
            },
            "clusters": [
                {
                    "step": c.step,
                    "count": c.count,
                    "percentage": round(c.percentage, 1),
                    "rules": len(c.rules),
                    "preventable": c.preventable_count,
                }
                for c in analysis.clusters
            ],
            "rules": {
                "total": len(rules),
                "by_confidence": by_confidence,
            },
            "triggers": [
                {
                    "name": t.name,
                    "met": t.met,
                    "current_value": t.current_value,
                    "threshold": t.threshold,
                }
                for t in triggers
            ],
            "last_resynthesis": (
                config.last_resynthesis_date.isoformat()
                if config.last_resynthesis_date
                else None
            ),
        }

    # -------------------------------------------------------------------
    # GET /api/corrections
    # -------------------------------------------------------------------
    @app.get("/api/corrections")
    def list_corrections(
        step: str | None = Query(None),
        since: str | None = Query(None),
    ):
        config = _config()
        corrections = load_corrections(config)

        if step:
            corrections = [c for c in corrections if c.get("step") == step]

        if since:
            try:
                since_dt = datetime.fromisoformat(since)
                filtered = []
                for c in corrections:
                    d = c.get("date")
                    if isinstance(d, datetime) and d >= since_dt:
                        filtered.append(c)
                    elif isinstance(d, str) and d >= since:
                        filtered.append(c)
                corrections = filtered
            except ValueError:
                pass  # ignore malformed since param

        return [_serialize(c) for c in corrections]

    # -------------------------------------------------------------------
    # GET /api/corrections/{corr_id}
    # -------------------------------------------------------------------
    @app.get("/api/corrections/{corr_id}")
    def get_correction(corr_id: str):
        config = _config()
        corrections = load_corrections(config)
        for c in corrections:
            if c.get("id") == corr_id:
                return _serialize(c)
        raise HTTPException(status_code=404, detail=f"Correction '{corr_id}' not found")

    # -------------------------------------------------------------------
    # POST /api/corrections
    # -------------------------------------------------------------------
    @app.post("/api/corrections", status_code=201)
    def create_correction(body: CorrectionCreate):
        config = _config()
        corrections = load_corrections(config)

        corr_id = next_id(corrections, "corr")
        now = datetime.now(timezone.utc)

        correction: dict[str, Any] = {
            "id": corr_id,
            "subject": body.subject,
            "date": now,
            "protocol_version": config.protocol_version,
            "step": body.step,
            "protocol_output": body.protocol_output,
            "correct_output": body.correct_output,
            "reasoning": body.reasoning,
        }
        if body.rule:
            correction["rule"] = body.rule

        corrections.append(correction)
        save_corrections(config, corrections)

        # Extract rule if present
        if body.rule:
            rule = extract_rule(correction, config)
            if rule is not None:
                rules = load_rules(config)
                rules.append(rule)
                save_rules(config, rules)

        return _serialize(correction)

    # -------------------------------------------------------------------
    # GET /api/triggers
    # -------------------------------------------------------------------
    @app.get("/api/triggers")
    def get_triggers():
        config = _config()
        corrections = load_corrections(config)
        rules = load_rules(config)
        results = evaluate_triggers(config, corrections, rules)
        return [
            {
                "name": t.name,
                "met": t.met,
                "current_value": t.current_value,
                "threshold": t.threshold,
            }
            for t in results
        ]

    # -------------------------------------------------------------------
    # GET /api/protocol
    # -------------------------------------------------------------------
    @app.get("/api/protocol")
    def get_protocol():
        config = _config()
        proto_path = config.root / config.protocol_path

        if proto_path.is_dir():
            modules = []
            for f in sorted(proto_path.glob("*.md")):
                modules.append({
                    "name": f.name,
                    "content": f.read_text(),
                })
            return {
                "path": str(config.protocol_path),
                "version": config.protocol_version,
                "type": "directory",
                "modules": modules,
            }
        else:
            return {
                "path": str(config.protocol_path),
                "version": config.protocol_version,
                "type": "file",
                "content": proto_path.read_text(),
            }

    # -------------------------------------------------------------------
    # GET /api/protocol/versions
    # -------------------------------------------------------------------
    @app.get("/api/protocol/versions")
    def list_versions():
        config = _config()
        versions_dir = config.root / config.archive_versions_path
        if not versions_dir.exists():
            return []

        result = []
        for f in sorted(versions_dir.iterdir()):
            if f.is_file() and f.suffix == ".md":
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                result.append({
                    "version": f.stem,
                    "filename": f.name,
                    "modified": mtime.isoformat(),
                })
        return result

    # -------------------------------------------------------------------
    # POST /api/resynthesis
    # -------------------------------------------------------------------
    @app.post("/api/resynthesis")
    def post_resynthesis(run: bool = Query(False)):
        config = _config()
        corrections = load_corrections(config)
        rules = load_rules(config)
        analysis = analyze_corrections(corrections, rules)

        proto_path = config.root / config.protocol_path
        if proto_path.is_dir():
            parts = []
            for f in sorted(proto_path.glob("*.md")):
                parts.append(f"--- MODULE: {f.name} ---\n{f.read_text()}")
            protocol_content = "\n\n".join(parts)
        else:
            protocol_content = proto_path.read_text()

        prompt = assemble_prompt(config, protocol_content, corrections, rules, analysis)

        if not run:
            return {"prompt": prompt}

        try:
            new_protocol = run_resynthesis(config, prompt)
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="LLM provider not installed. Install with: pip install protolab[ai]",
            )
        except RuntimeError as e:
            logger.error("Resynthesis failed: %s", e)
            raise HTTPException(status_code=500, detail="Resynthesis execution failed")

        staged_path = stage_resynthesis(config, new_protocol)
        return {
            "prompt": prompt,
            "staged_path": str(staged_path.relative_to(config.root)),
            "staged_content": new_protocol,
        }

    # -------------------------------------------------------------------
    # POST /api/resynthesis/promote
    # -------------------------------------------------------------------
    @app.post("/api/resynthesis/promote")
    def post_promote(version: str = Query(...)):
        config = _config()
        staged_dir = config.root / "resynthesis"
        staged_files = list(staged_dir.glob("staged-*.md")) if staged_dir.exists() else []
        if not staged_files:
            raise HTTPException(status_code=404, detail="No staged resynthesis found")

        staged_path = staged_files[-1]  # most recent
        promote_resynthesis(config, staged_path, version)
        return {"version": version, "status": "promoted"}

    # -------------------------------------------------------------------
    # PATCH /api/config
    # -------------------------------------------------------------------
    @app.patch("/api/config")
    def patch_config(body: ConfigPatch):
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib
        import tomli_w

        config_file = app.state.config_path
        with open(config_file, "rb") as f:
            data = tomllib.load(f)

        triggers = data.setdefault("resynthesis", {}).setdefault("triggers", {})
        if body.total_corrections is not None:
            triggers["total_corrections"] = body.total_corrections
        if body.cluster_threshold is not None:
            triggers["cluster_threshold"] = body.cluster_threshold
        if body.preventable_errors is not None:
            triggers["preventable_errors"] = body.preventable_errors
        if body.max_days_since_resynthesis is not None:
            triggers["max_days_since_resynthesis"] = body.max_days_since_resynthesis

        config_file.write_text(tomli_w.dumps(data))

        config = _config()
        return {
            "total_corrections": config.triggers.total_corrections,
            "cluster_threshold": config.triggers.cluster_threshold,
            "preventable_errors": config.triggers.preventable_errors,
            "max_days_since_resynthesis": config.triggers.max_days_since_resynthesis,
        }

    # -------------------------------------------------------------------
    # GET /api/events (SSE)
    # -------------------------------------------------------------------
    _sse_connections = 0

    @app.get("/api/events")
    async def event_stream():
        nonlocal _sse_connections
        if _sse_connections >= MAX_SSE_CONNECTIONS:
            raise HTTPException(status_code=503, detail="Too many SSE connections")

        async def generate():
            nonlocal _sse_connections
            _sse_connections += 1
            try:
                config = _config()
                corr_path = config.root / config.corrections_path
                rules_path = config.root / config.rules_path
                config_file = app.state.config_path

                mtimes = {
                    "corrections": _mtime(corr_path),
                    "rules": _mtime(rules_path),
                    "config": _mtime(config_file),
                }
                prev_corr_ids = {c.get("id") for c in load_corrections(config)}
                last_ping = time.monotonic()

                while True:
                    await asyncio.sleep(POLL_INTERVAL)

                    # Check corrections
                    new_mt = _mtime(corr_path)
                    if new_mt != mtimes["corrections"]:
                        mtimes["corrections"] = new_mt
                        config = _config()
                        current = load_corrections(config)
                        current_ids = {c.get("id") for c in current}
                        new_ids = current_ids - prev_corr_ids
                        for c in current:
                            if c.get("id") in new_ids:
                                yield f"event: correction_added\ndata: {json.dumps(_serialize(c))}\n\n"

                        # Check triggers on correction change
                        rules = load_rules(config)
                        triggers = evaluate_triggers(config, current, rules)
                        for t in triggers:
                            if t.met:
                                yield f"event: trigger_met\ndata: {json.dumps({'name': t.name, 'current_value': t.current_value, 'threshold': t.threshold})}\n\n"

                        prev_corr_ids = current_ids

                    # Check rules
                    new_mt = _mtime(rules_path)
                    if new_mt != mtimes["rules"]:
                        mtimes["rules"] = new_mt
                        yield f"event: rules_changed\ndata: {json.dumps({'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

                    # Check config
                    new_mt = _mtime(config_file)
                    if new_mt != mtimes["config"]:
                        mtimes["config"] = new_mt
                        config = _config()
                        yield f"event: config_changed\ndata: {json.dumps({'version': config.protocol_version})}\n\n"

                    # Keepalive
                    if time.monotonic() - last_ping > 15:
                        yield ": ping\n\n"
                        last_ping = time.monotonic()
            finally:
                _sse_connections -= 1

        return StreamingResponse(generate(), media_type="text/event-stream")

    # -------------------------------------------------------------------
    # GET / (dashboard)
    # -------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    def dashboard():
        return DASHBOARD_HTML

    return app


# ---------------------------------------------------------------------------
# Dashboard HTML
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Protolab</title>
<style>
  :root { --bg: #1a1a2e; --surface: #16213e; --border: #0f3460; --text: #e0e0e0;
    --accent: #e94560; --ok: #4ecca3; --dim: #888; --warn: #f5a623; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'SF Mono', 'Fira Code', monospace; background: var(--bg);
    color: var(--text); font-size: 14px; line-height: 1.5; }
  .header { padding: 16px 24px; border-bottom: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 18px; font-weight: 600; }
  .header .version { color: var(--dim); font-size: 13px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;
    padding: 16px 24px; height: calc(100vh - 60px); overflow: hidden; }
  .panel { background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 16px; overflow-y: auto; }
  .panel h2 { font-size: 14px; font-weight: 600; margin-bottom: 12px;
    color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
  .correction { border-bottom: 1px solid var(--border); padding: 10px 0; }
  .correction .meta { color: var(--dim); font-size: 12px; margin-bottom: 4px; }
  .correction .step { color: var(--accent); font-weight: 600; }
  .correction .outputs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
    margin-top: 6px; font-size: 12px; }
  .correction .outputs .wrong { color: #e94560; }
  .correction .outputs .right { color: var(--ok); }
  .correction .reasoning { font-size: 12px; color: var(--dim); margin-top: 4px;
    font-style: italic; }
  .trigger { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
  .trigger .name { width: 160px; font-size: 12px; }
  .trigger .bar-bg { flex: 1; height: 8px; background: #0a0a1a; border-radius: 4px; }
  .trigger .bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
  .trigger .bar-fill.ok { background: var(--ok); }
  .trigger .bar-fill.met { background: var(--accent); }
  .trigger .value { width: 60px; text-align: right; font-size: 12px; color: var(--dim); }
  .cluster-table { width: 100%; font-size: 12px; border-collapse: collapse; }
  .cluster-table th { text-align: left; color: var(--dim); padding: 4px 8px;
    border-bottom: 1px solid var(--border); }
  .cluster-table td { padding: 4px 8px; }
  .config-form label { display: block; font-size: 12px; color: var(--dim); margin-top: 8px; }
  .config-form input { background: #0a0a1a; border: 1px solid var(--border);
    color: var(--text); padding: 4px 8px; border-radius: 4px; width: 100%;
    font-family: inherit; margin-top: 2px; }
  .btn { background: var(--accent); color: white; border: none; padding: 6px 14px;
    border-radius: 4px; cursor: pointer; font-family: inherit; font-size: 12px;
    margin-top: 10px; }
  .btn:hover { opacity: 0.85; }
  .empty { color: var(--dim); font-style: italic; padding: 20px 0; }
  .rules-summary { font-size: 12px; margin-top: 12px; }
  .rules-summary span { margin-right: 12px; }
  .rules-summary .structural { color: var(--ok); }
  .rules-summary .strong_pattern { color: var(--warn); }
  .rules-summary .provisional { color: var(--dim); }
  .flash { animation: flash 0.5s ease-out; }
  @keyframes flash { from { background: rgba(233,69,96,0.2); } to { background: transparent; } }
</style>
</head>
<body>
<div class="header">
  <h1>protolab <span class="version" id="proto-version"></span></h1>
  <span class="version" id="proto-modified"></span>
</div>
<div class="grid">
  <div class="panel" id="corrections-panel">
    <h2>Corrections <span id="corr-count" style="color:var(--dim);font-weight:400"></span></h2>
    <div id="corrections-list"></div>
  </div>
  <div class="panel">
    <h2>Triggers</h2>
    <div id="triggers-list"></div>
    <h2 style="margin-top:20px">Clusters</h2>
    <table class="cluster-table" id="cluster-table">
      <thead><tr><th>Step</th><th>Count</th><th>%</th><th>Rules</th><th>Prev.</th></tr></thead>
      <tbody id="cluster-body"></tbody>
    </table>
    <div class="rules-summary" id="rules-summary"></div>
  </div>
  <div class="panel">
    <h2>Configuration</h2>
    <form class="config-form" id="config-form">
      <label>Total corrections threshold
        <input type="number" name="total_corrections" id="cfg-total">
      </label>
      <label>Cluster threshold (0-1)
        <input type="number" step="0.05" name="cluster_threshold" id="cfg-cluster">
      </label>
      <label>Preventable errors threshold
        <input type="number" name="preventable_errors" id="cfg-preventable">
      </label>
      <label>Max days since resynthesis
        <input type="number" name="max_days_since_resynthesis" id="cfg-days">
      </label>
      <button type="submit" class="btn">Save</button>
    </form>
    <h2 style="margin-top:20px">Protocol</h2>
    <div id="protocol-info" style="font-size:12px;color:var(--dim)"></div>
    <h2 style="margin-top:20px">Last Resynthesis</h2>
    <div id="last-resynth" style="font-size:12px;color:var(--dim)">None</div>
  </div>
</div>
<script>
const API = '';

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s));
  return d.innerHTML;
}

function renderCorrection(c) {
  return `<div class="correction flash">
    <div class="meta"><span class="step">${esc(c.step)}</span> &middot; ${esc(c.subject)} &middot; ${c.date ? esc(c.date.substring(0,10)) : ''} &middot; <span style="color:var(--dim)">${esc(c.id)}</span></div>
    <div class="outputs">
      <div class="wrong">${esc(c.protocol_output)}</div>
      <div class="right">${esc(c.correct_output)}</div>
    </div>
    <div class="reasoning">${esc(c.reasoning)}</div>
  </div>`;
}

function renderTrigger(t) {
  const pct = t.threshold > 0 ? Math.min(100, (t.current_value / t.threshold) * 100) : 0;
  const cls = t.met ? 'met' : 'ok';
  return `<div class="trigger">
    <span class="name">${t.name}</span>
    <div class="bar-bg"><div class="bar-fill ${cls}" style="width:${pct}%"></div></div>
    <span class="value">${t.current_value}/${t.threshold}</span>
  </div>`;
}

async function refresh() {
  try {
    const res = await fetch(API + '/api/status');
    const d = await res.json();

    document.getElementById('proto-version').textContent = d.protocol.version;
    document.getElementById('proto-modified').textContent = d.protocol.last_modified ? 'Modified ' + d.protocol.last_modified.substring(0,10) : '';
    document.getElementById('corr-count').textContent = '(' + d.corrections.total + ')';
    document.getElementById('last-resynth').textContent = d.last_resynthesis || 'None';

    // Triggers
    document.getElementById('triggers-list').innerHTML = d.triggers.map(renderTrigger).join('');

    // Clusters
    document.getElementById('cluster-body').innerHTML = d.clusters.map(c =>
      `<tr><td>${esc(c.step)}</td><td>${c.count}</td><td>${c.percentage}%</td><td>${c.rules}</td><td>${c.preventable}</td></tr>`
    ).join('');

    // Rules summary
    const rc = d.rules.by_confidence || {};
    document.getElementById('rules-summary').innerHTML =
      `<span>${d.rules.total} rules:</span>` +
      Object.entries(rc).map(([k,v]) => `<span class="${esc(k)}">${v} ${esc(k)}</span>`).join('');

    // Config
    const triggers = {};
    d.triggers.forEach(t => triggers[t.name] = t);
    document.getElementById('cfg-total').value = triggers['total_corrections']?.threshold ?? '';
    document.getElementById('cfg-cluster').value = triggers['cluster_threshold']?.threshold ?? '';
    document.getElementById('cfg-preventable').value = triggers['preventable_errors']?.threshold ?? '';
    document.getElementById('cfg-days').value = triggers['days_since_resynthesis']?.threshold ?? '';

    // Protocol info
    document.getElementById('protocol-info').textContent = d.protocol.path;

    // Corrections (full list on initial load)
    const cres = await fetch(API + '/api/corrections');
    const corrections = await cres.json();
    document.getElementById('corrections-list').innerHTML =
      corrections.length ? corrections.reverse().map(renderCorrection).join('')
      : '<div class="empty">No corrections yet.</div>';
  } catch(e) {
    console.error('Refresh failed:', e);
  }
}

// SSE live updates
function connectSSE() {
  const es = new EventSource(API + '/api/events');
  es.addEventListener('correction_added', (e) => {
    const c = JSON.parse(e.data);
    const list = document.getElementById('corrections-list');
    const empty = list.querySelector('.empty');
    if (empty) empty.remove();
    list.insertAdjacentHTML('afterbegin', renderCorrection(c));
    // Update count
    const countEl = document.getElementById('corr-count');
    const current = parseInt(countEl.textContent.replace(/[()]/g,'')) || 0;
    countEl.textContent = '(' + (current + 1) + ')';
    // Refresh triggers and clusters
    fetch(API + '/api/status').then(r => r.json()).then(d => {
      document.getElementById('triggers-list').innerHTML = d.triggers.map(renderTrigger).join('');
      document.getElementById('cluster-body').innerHTML = d.clusters.map(c =>
        `<tr><td>${esc(c.step)}</td><td>${c.count}</td><td>${c.percentage}%</td><td>${c.rules}</td><td>${c.preventable}</td></tr>`
      ).join('');
    });
  });
  es.addEventListener('config_changed', () => refresh());
  es.addEventListener('trigger_met', (e) => {
    const t = JSON.parse(e.data);
    console.log('Trigger met:', t.name);
  });
  es.onerror = () => { es.close(); setTimeout(connectSSE, 5000); };
}

// Config form
document.getElementById('config-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const body = {};
  const total = document.getElementById('cfg-total').value;
  const cluster = document.getElementById('cfg-cluster').value;
  const prev = document.getElementById('cfg-preventable').value;
  const days = document.getElementById('cfg-days').value;
  if (total) body.total_corrections = parseInt(total);
  if (cluster) body.cluster_threshold = parseFloat(cluster);
  if (prev) body.preventable_errors = parseInt(prev);
  if (days) body.max_days_since_resynthesis = parseInt(days);
  await fetch(API + '/api/config', {
    method: 'PATCH', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  refresh();
});

refresh();
connectSSE();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Server runner
# ---------------------------------------------------------------------------

def run_server(config_path: Path, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
    """Create the app and run it with uvicorn."""
    import uvicorn

    app = create_app(config_path)
    uvicorn.run(app, host=host, port=port)
