# Fix Issues Plan

Issues found while updating the README on 2026-09-24. None of them has been fixed yet. Each entry gives the problem, its effect, and a suggested fix.

## 1. HTTPS enforcement doesn't skip the real health endpoint
- **Where:** [app/middlewares.py:217](app/middlewares.py#L217)
- **Problem:** the middleware skips HTTPS enforcement only when `request.url.path == "/health"`. The actual route is `/v1/monitor/health` ([app/routers/healthRouters.py](app/routers/healthRouters.py)).
- **Effect:** with `ENFORCE_HTTPS=true`, plain-HTTP health checks (for example from a load balancer) get a `307` redirect instead of a health response.
- **Fix:** compare against `/v1/monitor/health` (or check `path.endswith("/monitor/health")`).

## 2. Deploy playbooks copy files that don't exist
- **Where:** [deployment/raspberry/windfire-calendar-deploy.yaml](deployment/raspberry/windfire-calendar-deploy.yaml) and [windfire-calendar-full-deploy.yaml](deployment/raspberry/windfire-calendar-full-deploy.yaml), Tasks 6 and 7
- **Problem:** the tasks copy `../../setenv.sh` and `../../commons.sh`. Neither exists; the repo has only `common.sh`.
- **Effect:** the deployment fails at Task 6. Even if those tasks are skipped, the scripts on the Pi `source ../common.sh`, which is never copied.
- **Fix:** replace both tasks with a single task that copies `../../common.sh` to `{{ remote_windfire_calendar_dir }}`.

## 3. Full-deploy playbook has invalid YAML
- **Where:** [deployment/raspberry/windfire-calendar-full-deploy.yaml:3](deployment/raspberry/windfire-calendar-full-deploy.yaml#L3)
- **Problem:** the line reads `- host- hosts: calendar_service`.
- **Effect:** the playbook fails to parse.
- **Fix:** change it to `- hosts: calendar_service`. Also note that `deploy.sh` runs only `windfire-calendar-deploy.yaml`, so the full-deploy playbook can't be run from the scripts. Consider adding an option for it.

## 4. The certificate script can't handle the Test environment
- **Where:** [app/ssl/generateServerCert.sh](app/ssl/generateServerCert.sh)
- **Problem:**
  - `selectEnvironment` sets `ENVIRONMENT=test` for option 2, but `main` accepts only `dev|staging|prod`. Choosing Test exits with "Invalid environment".
  - The invalid-selection branch calls `getEnvironment`, which isn't defined.
  - The local `selectEnvironment` duplicates the one in [common.sh](common.sh).
- **Fix:** replace `staging` with `test` in the `case`, remove the local `selectEnvironment`, and use the one from `common.sh`.

## 5. Default ports don't match between the test client and the server
- **Where:** [test/test.py](test/test.py) (`calendarServerPort = "8444"`), the help text in [test/run-test.sh](test/run-test.sh), and [app/.env_PLACEHOLDER](app/.env_PLACEHOLDER) (`API_PORT_SECURE=8443`)
- **Effect:** running `./run-test.sh` without `-p` fails to connect to a server started with the template configuration.
- **Fix:** pick one HTTPS port (8443 or 8444) and use it in `test.py`, `run-test.sh` and `.env_PLACEHOLDER`. Then remove the port note from the "Test the REST API" section of the README.

## 6. The terminal menu prompt shows the wrong range
- **Where:** [app/calendarMgr.py](app/calendarMgr.py), `getChoice()`
- **Problem:** the prompt says `Enter your choice (1-4)`, but the menu has 5 options (5 = Exit).
- **Fix:** change the prompt to `(1-5)`.

## 7. Deployment copies local secrets without saying so
- **Where:** [windfire-calendar-deploy.yaml](deployment/raspberry/windfire-calendar-deploy.yaml), Task 4 (rsync of `app/`)
- **Problem:** `app/.env`, `app/credentials.json` and `app/token.json` are gitignored but aren't excluded from the rsync, so the deploy ships whatever local copies exist. The production setup therefore depends on the developer's local files: `.env` may contain dev values (for example placeholder SSL paths), and a missing `token.json` means the Google OAuth consent flow would need a browser on the Pi.
- **Fix:** exclude these files from the rsync and copy production versions explicitly, for example with a dedicated task that reads from a local production config folder, or with Ansible Vault for secrets. Update the README deployment section to match.

## Minor items noticed along the way
- [app/start-apicalendar.sh](app/start-apicalendar.sh): the help text says the script sources `../setenv.sh` and `../commons.sh`. It sources only `../common.sh`.
- [app/stop-apicalendar.sh](app/stop-apicalendar.sh): `getPid` ends with `return $pid` (lowercase, undefined variable), and it uses `kill -9` where `kill -TERM` would allow a clean shutdown.
- [app/logger/loggerFactory.py](app/logger/loggerFactory.py): `interval=1 / 86400` is a fractional interval. `DEFAULT_LOG_BACKUP_COUNT` and `DEFAULT_LOG_ROTATION_INTERVAL` from `.env` are ignored (`backupCount=7` is hardcoded). A stream handler is created but never attached, so nothing is logged to the console.
- [app/config/settings.py](app/config/settings.py): `key in 'ENFORCE_HTTPS'` and `key in 'API_PORT'` do substring checks on a string. They should be equality checks (for example, `get('PORT')` would match `'API_PORT'`).
- [app/utils/dateMgr.py](app/utils/dateMgr.py): `getDate()` calls `datetime.datetime(...)`, but `datetime` is imported as the class, so the call would raise `AttributeError`. The function is currently unused.
- [test/installPrereqs.sh](test/installPrereqs.sh): pins `pydantic==2.5.0` while the app uses `2.13.5`, and doesn't quote `uvicorn[standard]==0.24.0`, so zsh treats the brackets as a glob.
- [deployment/deploy.sh](deployment/deploy.sh) doesn't export `ANSIBLE_CONFIG`, while `undeploy.sh` does.
