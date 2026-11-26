# Unified Maintenance Panel — proof-of-concept brief

This is the brief for building the proof of concept on top of the hello-world
scaffold in this repo. Read `README.md` first and run both halves locally
before changing anything.

## What this is

An internal web app, one page for each kind of thing, that shows every PROMS
server and instance, what they're doing, and whether anything needs attention.
It replaces information that is currently spread across Slack webhook
messages, a landing page per server, a tracking spreadsheet and ad-hoc shell
loops. It will later be the place audit evidence is pulled from.

Users: Radley's technical staff (fewer than ten people). Internal only.

## Ground rules

1. **The panel never holds SSH keys or server credentials.** It reads state
   over HTTPS from a status file each server publishes, and receives events
   that the servers push to it. Anything that *does* something on a server
   goes through GitHub Actions, not through the panel.
2. **Python 3.9 compatible** backend (Rocky 9 ships 3.9). FastAPI, Pydantic 2,
   httpx, APScheduler, psycopg. No ORM beyond what you need; plain SQL in a
   small repository module is fine.
3. **Vue 3 + Vite** frontend, `<script setup>`, no UI framework. Keep the
   existing look (`style.css`); it matches the other internal pages.
4. **No Docker.** It runs as a systemd service behind nginx on Dart, deployed
   by Ansible, the same as everything else on the estate. `deploy/` has the
   unit and nginx snippet.
5. **Keep every call to the backend in `frontend/src/api.js`.** Keep every SQL
   statement in `backend/app/db.py`.
6. Don't invent server names, hostnames or instance names. `servers.yml` is
   the list; ask if something's missing.
7. Write tests for the backend (`pytest`, `httpx` test client) for the API
   endpoints and the status parser. Frontend tests are optional at this stage.
8. Commit in small steps on a branch. Don't push without asking.

## Phase 1 — read-only dashboard (this POC)

### 1. Persist state in Postgres

Replace the in-memory `status` and `events` with Postgres tables. Connection
from `UMP_DATABASE_URL`. Provide `backend/schema.sql` and apply it on startup
if the tables don't exist.

```
servers      name, zone, role, url, status_url          (loaded from servers.yml, upserted on start)
server_status server_name, checked_at, state, payload jsonb   (one row per poll; keep 7 days)
events       id, received_at, source, instance, kind, level, message, data jsonb
```

`GET /api/servers` returns each server with its **latest** status row.
`GET /api/events` supports `?source=&instance=&kind=&since=&limit=`.

### 2. Richer status from each server

`server_info.py` today publishes `serverinfo.json` on Frost (see the shape in
`backend/app/main.py`). Extend the **reader** side here to accept these
additional optional sections, so the server-side script can grow
independently:

```json
"disks":    [{"mount": "/", "size_gb": 999, "used_gb": 333, "pct": 34, "archive": false}],
"services": {"tomcat": "active", "postgresql": "active", "nginx": "active"},
"cert":     {"subject": "*.radleypropertysolutions.com", "not_after": "2027-06-07T23:59:59Z"},
"backups":  [{"instance": "jpmorgan", "last_ok": "2026-11-25T02:10:00Z", "size_gb": 1.2}],
"updates":  {"security_pending": 3, "checked": "..."},
"crons":    [{"user": "root", "schedule": "0 2 * * *", "command": "/home/tech/scripts/full_backup.sh ..."}]
```

Health rule, in one function with tests:

| light | when |
|---|---|
| red | unreachable, or any service not active, or any non-archive disk ≥ 90%, or cert < 7 days, or a backup > 36 h old |
| amber | any non-archive disk ≥ 80%, cert < 30 days, security updates pending, status older than 3 × poll interval |
| green | otherwise |
| grey | `status_url` not set |

Disks flagged `archive: true` never affect the light.

### 3. Pages

Vue Router, four pages:

- **Overview** (the current page): server cards with the light, and the
  activity feed. Cards link to the server page.
- **Server**: everything from the status JSON laid out: disks, services,
  cert, backups, crons, instances. Status history for the last 24 h as a
  simple list.
- **Instance**: the instance's config (threads, DB name, paths from the
  status JSON) and its events only.
- **Activity**: the full event feed with filters by server, instance, kind,
  level and date.

### 4. Events from the webhook scripts

Document, in `docs/events.md`, the JSON each existing script should POST, one
per kind: `login`, `cashflow`, `backup`, `deploy`, `disk`, `cert`. Include a
`bash` snippet using `curl` that `slack_notify.sh` can call after it posts to
Slack. The backend must accept events with unknown `kind` values (store them,
show them) so a new script doesn't need a backend change.

Add a shared-secret header (`X-UMP-Token`, from `UMP_EVENT_TOKEN`) that
`POST /api/events` requires. Reject without it.

### 5. Done when

- `pytest` passes.
- Both halves run locally per the README, with Postgres on localhost.
- A fake status JSON served from a local file (document how) shows a server
  going green → amber → red as the file is edited.
- A posted event appears on the Overview, the Instance page and the Activity
  page with filters working.
- `README.md` updated; `docs/events.md` written.

## Not in this phase

Login (phase 2: Entra ID via OIDC — note where it will hook in, don't build
it). Log viewing. Running anything on a server. Selenide (phase 3: a tab that
triggers a GitHub Actions `workflow_dispatch` and links to the Allure report).
Retiring the Slack webhooks or the per-instance maintenance panels.

## Questions to ask before guessing

- Anything about the shape of `serverinfo.json` beyond what's in `main.py`.
- Which Postgres version to target (13 on the new servers).
- Whether a server in `servers.yml` should be grouped differently.
