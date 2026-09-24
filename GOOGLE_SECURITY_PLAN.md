# Fix: `FileNotFoundError: credentials.json` when running run-calendar.sh

## Context
`calendarService.authenticate()` ([app/services/calendarService.py:29-67](app/services/calendarService.py)) reads the Google OAuth client file `credentials.json` from the current working directory (`app/`) when no valid `token.json` exists. That file is gitignored and doesn't exist anywhere on disk. The code isn't what's broken: the Google OAuth client secret was never created or copied in. On top of that, the code crashes with a raw traceback and gives no hint about what to do.

Also found: `app/.env` still has `DEFAULT_LOG_FILE=<PUT_LOG_FILE_PATH_HERE>`, so logs are being written to a file literally named `<PUT_LOG_FILE_PATH_HERE>` inside `app/`.

## Step 0: save this plan
Copy this plan to `/Users/robertopozzi/dev/windfire-calendar/PLAN.md` (project root) before doing anything else.

## Step 1: user action (required, can't be done in code)
Create the OAuth client and put it in place:
1. Google Cloud Console → pick or create a project → **APIs & Services → Library** → enable **Google Calendar API**.
2. **OAuth consent screen**: set it up as External, add your Google account as a **Test user**, and add the scope `.../auth/calendar.readonly`.
3. **Credentials → Create credentials → OAuth client ID → Application type: Desktop app** → Download JSON.
4. Save it as `app/credentials.json`.
5. On the first run a browser opens for consent, and `app/token.json` gets created. Later runs reuse it.

## Step 2: code hardening in `app/services/calendarService.py`
- Resolve the file paths from settings, with defaults relative to the `app/` directory rather than the CWD:
  - `GOOGLE_CREDENTIALS_FILE` (default `<app_dir>/credentials.json`)
  - `GOOGLE_TOKEN_FILE` (default `<app_dir>/token.json`)
  - Use the existing `settings.get()` from [app/config/settings.py](app/config/settings.py).
- Add a small helper `_run_oauth_flow()` that runs the two duplicated `InstalledAppFlow` blocks. Before running, it checks that the credentials file exists. If it's missing, it logs an error and raises a `FileNotFoundError` whose message gives the expected path and the short setup steps above.
- In [app/handler/actionHandler.py](app/handler/actionHandler.py) / [app/calendarMgr.py](app/calendarMgr.py), catch that error at the top level. It then prints the friendly message in red (colorama is already used) and exits cleanly instead of showing a traceback.

## Step 3: config files
- `app/.env_PLACEHOLDER`: add a `# Google OAuth Configuration` section with `GOOGLE_CREDENTIALS_FILE=./credentials.json` and `GOOGLE_TOKEN_FILE=./token.json`.
- `app/.env`: set `DEFAULT_LOG_FILE=./logs/windfire-calendar.log`, which `.gitignore` already covers through `windfire-calendar.log*`. Delete the two stray `app/<PUT_LOG_FILE_PATH_HERE>*` files.
- README.md: add a short "Google Calendar API credentials" setup section covering the Step 1 instructions.

## Verification
1. Without `credentials.json`: run `./run-calendar.sh 1`, then option 1. Expect the clear error message and no traceback.
2. After adding `credentials.json`: the same flow opens the browser for consent, `token.json` gets created, and the event count for "Palestra" 2026 prints.
3. Run it again: no browser this time, because the token is reused. Check that logs go to `app/logs/windfire-calendar.log`.
