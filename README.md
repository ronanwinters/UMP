# Unified Maintenance Panel

One place to see every PROMS server and instance, what they're doing, and
whether anything needs attention. Internal use only.

```
ump/
├── backend/            FastAPI (Python 3.9+)
│   ├── app/main.py     the API and the background poller
│   ├── servers.yml     which servers to watch
│   └── requirements.txt
├── frontend/           Vue 3 + Vite
│   └── src/
│       ├── App.vue         page layout
│       ├── ServerCard.vue  one server + its instances
│       ├── EventFeed.vue   the activity table
│       └── api.js          every call to the backend, in one file
├── deploy/             systemd unit + nginx snippet for Dart (later)
└── POC_BRIEF.md        the brief for Claude Code to build the proof of concept
```

## How it fits together

```
 webhook scripts  ──POST /api/events──►  ┌──────────┐
 (login, cashflow, backup, deploy)       │ FastAPI  │ ◄──GET /api/*──  Vue UI
                                         │  :8000   │
 server_info.py on each server ◄──poll───┘
 (serverinfo.json over HTTPS)
```

- **Pull** for state: every `UMP_POLL_SECONDS` the backend fetches each
  server's `status_url` and keeps the result. The panel holds no SSH keys
  and no credentials to any server.
- **Push** for events: the existing `slack_notify.sh` scripts POST the same
  message to `/api/events` as well as to Slack.
- State is **in memory** in this hello-world. Postgres is the first thing the
  POC adds.

## Run it locally

Two terminals.

```bash
# 1. backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
#    http://localhost:8000/docs  <- FastAPI's auto-generated API explorer

# 2. frontend
cd frontend
npm install
npm run dev
#    http://localhost:5173
```

Vite proxies `/api/*` to port 8000, so the browser only ever talks to 5173.

Post a test event:

```bash
curl -X POST localhost:8000/api/events -H 'content-type: application/json' \
  -d '{"source":"bolt","instance":"jpmorgan","kind":"login","message":"jsmith logged in"}'
```

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `UMP_SERVERS_FILE` | `backend/servers.yml` | server list |
| `UMP_POLL_SECONDS` | `120` | how often to poll each server |

## Production shape (not yet wired)

`npm run build` writes static files to `frontend/dist/`. nginx on Dart serves
those and proxies `/api` to uvicorn running as a systemd service. See
`deploy/`. The panel sits behind the Edge firewall (office IPs only) and,
from phase 2, behind a login.
