"""
Unified Maintenance Panel - backend (hello-world scaffold).

What this does today:
  GET /api/health            -> {"ok": true}
  GET /api/servers           -> the list from servers.yml, each with its last
                                fetched status (or "not reporting")
  POST /api/events           -> accept a webhook event and keep it in memory
  GET /api/events            -> the last 200 events, newest first

A background job polls every server's status_url every POLL_SECONDS.
State is in memory only - fine for a hello world; Postgres comes next.

Run (from backend/):
  .venv/bin/uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

log = logging.getLogger("ump")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
SERVERS_FILE = Path(os.environ.get("UMP_SERVERS_FILE", BASE_DIR / "servers.yml"))
POLL_SECONDS = int(os.environ.get("UMP_POLL_SECONDS", "120"))

app = FastAPI(title="Unified Maintenance Panel", version="0.0.1")

# The Vite dev server runs on another port; allow it during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- state ----
servers: list[dict[str, Any]] = []          # from servers.yml
status: dict[str, dict[str, Any]] = {}      # name -> last poll result
events: deque[dict[str, Any]] = deque(maxlen=200)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_servers() -> None:
    global servers
    with open(SERVERS_FILE) as f:
        servers = yaml.safe_load(f)["servers"]
    log.info("loaded %d servers from %s", len(servers), SERVERS_FILE)


# -------------------------------------------------------------- polling ----
async def poll_one(client: httpx.AsyncClient, s: dict[str, Any]) -> None:
    name = s["name"]
    if not s.get("status_url"):
        status[name] = {"state": "not_reporting", "checked": now()}
        return
    try:
        r = await client.get(s["status_url"])
        r.raise_for_status()
        data = r.json()
        jvm_up = bool(data.get("jvm", {}).get("running"))
        status[name] = {
            "state": "ok" if jvm_up else "warn",
            "checked": now(),
            "generated": data.get("generated"),
            "server": data.get("server"),
            "jvm": data.get("jvm"),
            "snapshots": data.get("snapshots", []),
        }
    except Exception as e:                      # noqa: BLE001 - any failure = red
        status[name] = {"state": "error", "checked": now(), "error": str(e)[:200]}


async def poll_all() -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        await asyncio.gather(*(poll_one(client, s) for s in servers))
    log.info("polled %d servers", len(servers))


scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup() -> None:
    load_servers()
    scheduler.add_job(poll_all, "interval", seconds=POLL_SECONDS, next_run_time=datetime.now())
    scheduler.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    scheduler.shutdown(wait=False)


# ----------------------------------------------------------------- api -----
@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "time": now(), "servers": len(servers)}


@app.get("/api/servers")
def list_servers() -> list[dict[str, Any]]:
    return [{**s, "status": status.get(s["name"], {"state": "pending"})} for s in servers]


@app.post("/api/servers/poll", status_code=202)
async def poll_now() -> dict[str, str]:
    """Manual refresh button."""
    await poll_all()
    return {"result": "polled"}


class Event(BaseModel):
    """What the webhook scripts will POST. Mirrors the Slack message, structured."""
    source: str = Field(examples=["bolt"])               # server short name
    instance: str | None = Field(default=None, examples=["jpmorgan"])
    kind: str = Field(examples=["login", "cashflow", "backup", "deploy", "disk"])
    message: str
    level: str = Field(default="info", pattern="^(info|warn|error)$")
    data: dict[str, Any] | None = None


@app.post("/api/events", status_code=201)
def post_event(ev: Event) -> dict[str, Any]:
    rec = {"received": now(), **ev.model_dump()}
    events.appendleft(rec)
    return rec


@app.get("/api/events")
def list_events(limit: int = 50) -> list[dict[str, Any]]:
    if not 1 <= limit <= 200:
        raise HTTPException(400, "limit must be 1-200")
    return list(events)[:limit]
