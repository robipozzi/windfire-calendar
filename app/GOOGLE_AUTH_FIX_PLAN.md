# Fix Google `invalid_grant` on raspberry02 (windfire-calendar)

## Context
`/v1/calendar/events/count/year` fails on raspberry02 because the Google refresh token in `app/token.json` has been revoked or has expired (`invalid_grant`). The local `app/token.json` has `expiry 2026-10-01`, which means nothing has refreshed it for about 18 days. The most likely cause is that the Google Cloud OAuth consent screen is still in **Testing**. In Testing mode, Google expires refresh tokens after 7 days. Other ways a refresh token gets revoked: a password change, revoking access, or the 50-token-per-client limit.

There is a second problem. When the refresh fails, `CalendarService._runOAuthFlow()` ([calendarService.py:86-87](app/services/calendarService.py#L86-L87)) calls `flow.run_local_server()` on a headless Pi. The FastAPI handler is `async def` ([calendarRouters.py:16](app/routers/calendarRouters.py#L16)), so this blocking call freezes the event loop and the whole API hangs. The log stops at "Authenticating to Google..." because of this.

## Part 1: Get the service working again (ops, no code)
1. **Google Cloud Console > APIs & Services > OAuth consent screen**: set the Publishing status to **In production**. You don't need verification for personal use: with the `calendar.readonly` scope you will only see an "unverified app" warning during consent. This stops tokens from expiring every 7 days.
2. On the Mac, delete the old token and create a new one:
   `cd app && rm token.json && ./run-calendar.sh` → finish the browser consent → the app writes a new `app/token.json`.
3. Redeploy with `deployment/deploy.sh` (raspberry). [deploy-app.yaml](deployment/raspberry/tasks/deploy-app.yaml) Task 5 copies `token.json` with mode 0600, and the playbook stops and restarts the systemd service. This also clears the hung process.

## Part 2: Make it fail fast instead of hanging (code)
- [app/services/calendarService.py](app/services/calendarService.py):
  - Add `INTERACTIVE_AUTH = settings.get('GOOGLE_INTERACTIVE_AUTH')`, defaulting to true when the setting is unset, so the local CLI still works.
  - In `_runOAuthFlow()`, when interactive auth is disabled, log an error and raise `RuntimeError("Google token in <TOKEN_FILE> is expired or revoked; regenerate it locally (cd app && ./run-calendar.sh) and redeploy")` instead of calling `run_local_server`.
- [deployment/raspberry/templates/windfire-calendar.env.j2](deployment/raspberry/templates/windfire-calendar.env.j2): add `GOOGLE_INTERACTIVE_AUTH=false` in the Google OAuth section.
- No router changes are needed. The routers already turn the exception into an HTTP 500 that includes the message.
- `settings.get` returns a raw string for keys it doesn't special-case ([settings.py:20-50](app/config/settings.py#L20-L50)). Parse it in calendarService with the same convention as `ENFORCE_HTTPS`: `(settings.get('GOOGLE_INTERACTIVE_AUTH') or 'true').strip().lower() in ('true','1','yes','on')`.

## Verification
- Locally: `./run-calendar.sh` runs and lists events (the interactive path still works).
- After redeploy: call `POST https://raspberry02:8443/v1/calendar/events/count/year`. It should return 200 with a count. The service log should show a successful refresh/credentials load, and there should be no "Authenticating to Google" line.
- Negative test, run locally with `GOOGLE_INTERACTIVE_AUTH=false` and a corrupted `refresh_token` in a copy of the token file: the endpoint returns 500 with the regenerate message straight away, and other endpoints still respond (no hang).
- Recheck after more than 7 days to confirm the refresh token still works with the app in production.
