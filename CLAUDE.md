# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Windfire Calendar wraps the Google Calendar API and exposes it two ways from the same `app/` codebase:
1. **A terminal application** (`calendarMgr.py`) — an interactive menu for ad-hoc queries (count events by year/date range, list upcoming events).
2. **A secured FastAPI service** (`calendarApiServer.py`) — the same operations exposed as REST endpoints, protected by Bearer tokens issued/verified through the [windfire-security](../windfire-security) authentication service.

Both entry points share `services/calendarService.py`, `utils/dateMgr.py`, and the Google OAuth flow — the terminal app calls the service layer directly (`handler/actionHandler.py` → `calendarSrv`), while the API server calls it from `routers/calendarRouters.py` behind token verification.

This repo depends on the sibling repo `../windfire-security-client` (`$HOME/dev/windfire-security-client`) for the `client.authClient` module used to authenticate/verify tokens against the `windfire-security` server — see that repo's CLAUDE.md for how `authClient` resolves its target server and TLS settings.

## Running the terminal application

```bash
cd app
./run-calendar.sh          # prompts for environment (1=dev, 2=test, 3=prod)
./run-calendar.sh 1        # skip the prompt, run against dev
```

First run triggers Google's OAuth installed-app flow (opens a local browser callback on `flow.run_local_server`), reading `credentials.json` (Google OAuth client secret, not committed — must be obtained from Google Cloud Console) and caching the resulting token in `token.json` (both gitignored). Re-runs reuse/refresh `token.json` until it's invalid.

## Running the FastAPI service

```bash
cd app
./start-apicalendar.sh 1                    # dev environment, prompts for KEYCLOAK_CLIENT_SECRET
./start-apicalendar.sh 1 --LOG_LEVEL DEBUG  # with explicit log level
./run-apicalendar-background.sh <same args> # backgrounded, logs to logs/
./stop-apicalendar.sh
```

Note: `KEYCLOAK_CLIENT_SECRET` is prompted for and exported into the server process's environment (`inputKeycloakClientSecret` in `common.sh`), but nothing in `app/`'s Python code currently reads that variable — token verification is fully delegated to the `windfire-security` server via `commons.py`'s `verify_token()`, which only needs `KEYCLOAK_SERVICE` (from `.env`) and the incoming Bearer token. Don't assume this variable does anything without checking `commons.py` and `client.authClient` first.

First-time setup requires copying `app/.env_PLACEHOLDER` → `app/.env` (gitignored) and filling in `APP_NAME`, `API_HOST`/`API_PORT`/`API_PORT_SECURE`, `SSL_KEYFILE`/`SSL_CERTFILE`, `ENFORCE_HTTPS`, `ALLOWED_HOSTS`, `KEYCLOAK_SERVER_URL`, `KEYCLOAK_SERVICE` (the service name this app is registered as in `windfire-security`'s `service_config.json`, e.g. `windfire-calendar-srv`), plus `DEFAULT_LOG_LEVEL`/`DEFAULT_LOG_FILE`/rotation settings consumed by `logger/loggerFactory.py`.

## Environment / venv management

`app/createPythonVenv.sh` / `activatePythonVenv.sh` / `deactivatePythonVenv.sh` manage a venv named `windfire-calendar` (see `PYTHON_VIRTUAL_ENV` in `common.sh`); `test/` has its own equivalent trio for a `windfire-calendar-test` venv. Both `app/installPrereqs.sh` and `test/installPrereqs.sh` install the same pinned deps (FastAPI/uvicorn stack + Google API client libs) and then editable-install the sibling `windfire-security-client` package — **unless** the environment option passed through is `3` (prod), in which case they instead install a prebuilt wheel from `$HOME/dist/client-1.0.0-py3-none-any.whl`. That wheel must be built beforehand in `windfire-security-client` via its `createModule.sh`.

## Running tests

No automated/unit test suite — `test/test.py` is a manual integration script exercising a running FastAPI server end-to-end:

```bash
cd test
./run-test.sh              # prompts for env/credentials, hits health/auth/all calendar endpoints
./run-test.sh -p 9000      # against a non-default calendar server port
```

It authenticates via `client.authClient`, then calls `/v1/monitor/health`, `/v1/calendar/events/count/year`, `/count/today`, `/count/range`, and `/events/upcoming` in sequence, printing pass/fail for each. Test data is hardcoded (`event_title = "Palestra"`, fixed date ranges) — this is a smoke test against your own real Google Calendar, not a fixture-based test.

## Architecture of `app/`

Entry point `calendarApiServer.py` builds the FastAPI `app` and wires the same middleware stack as `windfire-security`'s server: CORS, `TrustedHostMiddleware` (gated on `ALLOWED_HOSTS`), GZip, and a custom `https_enforcement_middleware` (`middlewares.py`) that redirects HTTP→HTTPS except for `/health`-suffixed paths and adds HSTS/security headers. `main()` decides HTTP vs HTTPS uvicorn startup based on `ENFORCE_HTTPS` and whether `SSL_KEYFILE`/`SSL_CERTFILE` exist on disk.

Routing: `apiRouter.py` defines `api = APIRouter(prefix="/v1")`, including `routers/healthRouters.py` (`/v1/monitor/health`, unauthenticated) and `routers/calendarRouters.py` (`/v1/calendar/events/...`, all behind `Depends(verify_token)`). A `v2` router is declared but unused.

Authentication: `commons.py`'s `verify_token()` is the shared FastAPI dependency — it pulls the Bearer token via `HTTPBearer`, calls `authClient.verify(token, service=settings.get("KEYCLOAK_SERVICE"), method="remote")`, and raises 401 on failure. This is the only place auth happens; individual route handlers don't touch tokens directly. (Note the `method="remote"` argument is accepted by `authClient.verify()` but not actually forwarded over the wire — see `windfire-security-client`'s CLAUDE.md.)

Business logic: `services/calendarService.py`'s `CalendarService` (singleton `calendarSrv`) wraps `googleapiclient.discovery.build('calendar', 'v3', ...)`. Every public method calls `self.authenticate()` first, which lazily loads/refreshes `token.json` or runs the interactive OAuth flow — this makes the FastAPI endpoints not truly headless on a fresh box; the first API call after credentials expire will block waiting for a browser-based OAuth flow unless `token.json` is already valid. `utils/dateMgr.py` centralizes date parsing/formatting (ISO 8601 conversions, "is this a future date" checks) used by both the service and the terminal `handler/actionHandler.py`.

Terminal app: `calendarMgr.py` is a simple `while` loop presenting a 5-option menu, delegating each choice to `handler/actionHandler.py`, which collects/validates user input (year, date range, event title) and calls straight into `calendarSrv` — no HTTP involved.

Config/logging follow the same conventions as `windfire-security`: `config/settings.py` (`Settings`/`settings` singleton, `.env` via `python-dotenv`, with `ENFORCE_HTTPS`→bool and `API_PORT`/`API_PORT_SECURE`→int coercion) and `logger/loggerFactory.py` (always get loggers via `logger_factory.get_logger(<module_name>)`). Unlike `windfire-security`'s logger, this one reads `DEFAULT_LOG_FILE`/`DEFAULT_LOG_ROTATION_WHEN` from `settings` (i.e. from `.env`) rather than hardcoding a path — `.env` must set `DEFAULT_LOG_FILE` or the `TimedRotatingFileHandler` will fail to initialize.

## Certificates

`app/ssl/generateServerCert.sh` issues this service's TLS cert/key off the shared Windfire Root CA (created in `windfire-security`'s `ssl/createRootCA.sh`), using `openssl_config_localhost.ext` / `openssl_config_raspberry.ext` depending on target host. These are what `SSL_KEYFILE`/`SSL_CERTFILE` in `.env` point at.
