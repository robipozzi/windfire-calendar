# Plan: environment + Keycloak environment selection for windfire-calendar

## Context
Two requirements:
1. Every way of running the app must let the user choose the environment (Development / Test / Production).
2. `run-apicalendar.sh` and `run-apicalendar-background.sh` must let the user choose the Keycloak environment used for authentication (default Production = `raspberry01:8444`), with the endpoints configured in `app/.env`.

Current gaps found:
- `app/run-apicalendar-background.sh:28` hard-codes environment `3` — no choice.
- `app/run-apicalendar.sh` creates the venv (`createPythonVenv.sh "$RUN_ENVIRONMENT"`, line 22) *before* the interactive `selectEnvironment` (line 31), so when the env is picked at the prompt, `installPrereqs.sh` gets an empty option and always installs the dev (editable) client, even for Production. Same ordering issue in `app/run-calendar.sh`.
- `test/run-test.sh` only prompts; `parse_args` rejects any env argument, and `run` calls `selectEnvironment $1` with no arg.
- The Keycloak endpoint is hard-coded in the sibling repo `windfire-security-client/client/authClient.py:14-22` by `ENVIRONMENT` (dev→localhost:8443, prod→raspberry01:8444, test→empty host = broken). `KEYCLOAK_SERVER_URL` in `.env` is only logged, never used.

Decisions (from user): patch the client to accept host/port overrides; Keycloak envs Dev=`localhost:8444`, Test=`localhost:8444`, Prod=`raspberry01:8444`; interactive prompt (Enter = Production), also skippable with a flag.

## Changes

### 1. `windfire-security-client/client/authClient.py` (sibling repo)
In `AuthClient.__init__`, after the existing `ENVIRONMENT` mapping, let `KEYCLOAK_SERVER_HOST` / `KEYCLOAK_SERVER_PORT` env vars override host/port when set (port cast to int). Keep the current mapping as fallback so `run-auth-client.sh` and other consumers behave as before. Log the source of the values in the existing debug block. Update that repo's `CLAUDE.md` Architecture bullet accordingly.
Prod installs the wheel from `$HOME/dist`, so the wheel must be rebuilt with `./createModule.sh` (and redeployed) — note this in the README.

### 2. `app/.env` and `app/.env_PLACEHOLDER`
Replace `KEYCLOAK_SERVER_URL` with:
```
# Keycloak environments (windfire-security auth server) - selected at startup, default prod
KEYCLOAK_DEV_HOST=localhost
KEYCLOAK_DEV_PORT=8444
KEYCLOAK_TEST_HOST=localhost
KEYCLOAK_TEST_PORT=8444
KEYCLOAK_PROD_HOST=raspberry01
KEYCLOAK_PROD_PORT=8444
```
(placeholder file gets the same keys with these defaults). `.env` is already synced to the Pi by the deploy playbook, so no playbook change.

### 3. `common.sh` — new shared helpers
- `getEnvFileValue FILE KEY`: `grep "^KEY="`, strip inline `# comment`, surrounding whitespace/quotes. (Needed because `.env` can't be `source`d: `APP_NAME` has spaces and some lines have inline comments.)
- `selectKeycloakEnvironment [option]`: if option empty, prompt `1. Development 2. Test 3. Production [3]` (Enter → 3); accept `1|2|3` or `dev|test|prod`; re-prompt on invalid (same pattern as `selectEnvironment`/`setEnvironment`). Sets `KEYCLOAK_ENVIRONMENT`, then reads `KEYCLOAK_<ENV>_HOST/PORT` from `./.env` into `KEYCLOAK_SERVER_HOST` / `KEYCLOAK_SERVER_PORT`; print error and `exit 1` if missing.
- Add `KEYCLOAK_ENVIRONMENT=`, `KEYCLOAK_SERVER_HOST=`, `KEYCLOAK_SERVER_PORT=` to the variable section.

### 4. `app/run-apicalendar.sh`
- Rewrite `parseArguments` as a `while/case` loop: positional `1|2|3` (app env), `--LOG_LEVEL LEVEL`, new `--KEYCLOAK_ENV dev|test|prod` (or 1|2|3), `-h`, `-v`; unknown option → error + exit 1 (matches documented exit code).
- `main` order: parseArguments → `selectEnvironment "$RUN_ENVIRONMENT"` → `selectKeycloakEnvironment "$KEYCLOAK_ENV_OPTION"` → `source ./createPythonVenv.sh "$ENVIRONMENT_SELECTION"` → `run`. This fixes the wrong-prereqs bug.
- `run`: pass `KEYCLOAK_SERVER_HOST` / `KEYCLOAK_SERVER_PORT` (and `KEYCLOAK_ENVIRONMENT` for logging) to `python3 calendarApiServer.py`; include them in the "Starting server with" echo.
- Update `printHelp` (usage, `--KEYCLOAK_ENV`, examples, env var section).

### 5. `app/run-apicalendar-background.sh`
- Accept the same args (`[1|2|3] [--KEYCLOAK_ENV ENV] [--LOG_LEVEL LEVEL]`).
- Before backgrounding (output goes to a log, so no prompts are possible later): `selectEnvironment`, `selectKeycloakEnvironment`, `inputKeycloakClientSecret`; then launch `./run-apicalendar.sh $ENVIRONMENT_SELECTION --KEYCLOAK_ENV $KEYCLOAK_ENVIRONMENT [--LOG_LEVEL ...] > logs/windfire-calendar.log 2>&1 &`, so the child never prompts.
- Update the step list echoed at startup.

### 6. `app/run-calendar.sh`
Move `selectEnvironment $1` before `source ./createPythonVenv.sh`, and pass `$ENVIRONMENT_SELECTION` to it so prereqs match the chosen env. Fix `main $1` → `main "$@"`.

### 7. `test/run-test.sh`
Add `-e|--env 1|2|3` to `parse_args`, store in `RUN_ENVIRONMENT`, call `selectEnvironment "$RUN_ENVIRONMENT"` (prompts when omitted); update `print_help`.

### 8. `app/calendarApiServer.py`
Replace the `KEYCLOAK_SERVER_URL` log line (line 146) with `ENVIRONMENT`, `KEYCLOAK_ENVIRONMENT`, `KEYCLOAK_SERVER_HOST`, `KEYCLOAK_SERVER_PORT` via `os.getenv`.

### 9. `README.md`
Update the `.env` table (new `KEYCLOAK_*_HOST/PORT`, drop `KEYCLOAK_SERVER_URL`), the run-apicalendar usage (`[1|2|3] [--KEYCLOAK_ENV ENV] [--LOG_LEVEL LEVEL]`), the background script description (no longer Production-only), run-test `-e`, and a note to rebuild the client wheel.

## Verification
1. `bash -n` on every modified script.
2. `cd app && ./run-apicalendar.sh --help` shows new options; `./run-apicalendar.sh --bogus` exits 1.
3. `./run-apicalendar.sh` with no args: prompts for app env, then Keycloak env; Enter → `raspberry01:8444`. With `DEFAULT_LOG_LEVEL=DEBUG`, authClient debug log shows `https://raspberry01:8444` as base URL; choosing 1 shows `https://localhost:8444`.
4. `./run-apicalendar.sh 1 --KEYCLOAK_ENV dev --LOG_LEVEL DEBUG` → no prompts except the client secret; installs editable client.
5. `./run-apicalendar-background.sh` → prompts up front, returns; `logs/windfire-calendar.log` shows no prompts and the chosen env/Keycloak endpoint; stop with `./stop-apicalendar.sh`.
6. `./run-calendar.sh` and `test/run-test.sh -e 2` honor the env choice.
7. In windfire-security-client: `./run-auth-client.sh 1` still works (fallback path), then `./createModule.sh` to rebuild the wheel.
