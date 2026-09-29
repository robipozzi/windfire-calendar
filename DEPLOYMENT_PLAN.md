# Windfire Calendar – Deployment Procedure Review & Enhancement Plan

> **Status:** implemented on branch `feature/deployment`; on-Pi verification (steps 4–8) still to run.

## Context

`windfire-calendar/deployment/deploy.sh` has the same code as `windfire-security/deployment/deploy.sh`, with only the names changed.
It starts an ssh-agent, then runs `raspberry/windfire-calendar-deploy.yaml`. The playbook copies `app/` to the Pi and builds the venv, but it does **not start the service**.
The operator then has to SSH in and run `./run-apicalendar.sh 3 --KEYCLOAK_ENV prod`, typing the Keycloak client secret by hand.

`windfire-restaurants-backend` has a more mature version of the same Raspberry/Ansible pattern, and it becomes the target standard:

- a pre-flight chain before Ansible runs: build, check or generate the TLS cert/key, check or generate the truststore
- all secrets and endpoint values are collected once, up front, and exported as env vars that Ansible reads with `lookup('env', …)`
- the app runs as a supervised **systemd** service (`Restart=on-failure`, logs appended to a file)
- non-secret config comes from a **Jinja-templated env file** (`templates/*.env.j2`)
- secrets are **encrypted at rest with `systemd-creds`** (`/etc/credstore.encrypted`, `LoadCredentialEncrypted`) and never sit in plaintext on disk
- the private key and truststore are copied with mode `0600`
- the playbook ends with a **post-deploy check** (`wait_for` on the service port)
- the uninstall playbook stops and disables the unit, removes it, and runs `daemon-reload`

The house style shared by windfire-security and windfire-calendar is kept:

- `deployment/deploy.sh` / `undeploy.sh`
- `source ../common.sh`, with `selectDeploymentPlatform` and `PLATFORM_OPTION=$1`
- the bold blue banner, the `main → parseArgs → setFunction → $DEPLOY_FUNCTION` flow
- ssh-agent with `ansible_rsa` and `ANSIBLE_CONFIG=raspberry/ansible.cfg`
- `conf/config.yaml`, with `# Task N:` comments in the playbooks

The goal is one command that takes the calendar service to a running, self-restarting, health-checked service on `raspberry02`, with no secrets in plaintext.

## Review findings (current state)

### `deployment/deploy.sh` / `undeploy.sh`
1. **Broken fallback:** `setFunction` calls `selectDeploymentPlatform` again on an invalid platform but never sets `DEPLOY_FUNCTION` afterwards, so `$DEPLOY_FUNCTION` runs as an empty command.
2. **No error handling:** the `ansible-playbook` exit code is ignored and "Done" prints even when the deploy fails. `ssh-add` failure is also ignored.
3. **ssh-agent leak:** every run starts a new `ssh-agent` and never kills it.
4. **CWD-dependent:** it only works when started from `deployment/` (`source ../common.sh`, `raspberry/…`, `$PWD`).
5. **Unquoted `$@`**, and no `-h/--help`, even though `run-apicalendar.sh` already has a help pattern that could be reused.
6. **No pre-flight checks.** Nothing verifies that these exist before Ansible runs:
   - `app/.env`, `app/credentials.json`, `app/token.json`
   - the prod cert/key in `$HOME/opt/windfire/ssl/certs/raspberry`
   - the Windfire Root CA
   - the `windfire-security-client` wheel in `../windfire-security-client/dist`
   - the `ansible` / `ansible-playbook` binaries

   A missing file surfaces later as a failure in the middle of the playbook, or as a service that fails when it starts.

### `raspberry/windfire-calendar-deploy.yaml`
7. **The service is never started.** It is not supervised, not enabled at boot, and has no health check.
8. **The local `app/.env` is shipped as-is.** It is usually a dev config (`ALLOWED_HOSTS=localhost`, local SSL paths). There is no prod-specific templating.
9. **The Keycloak client secret is typed interactively on the Pi.** A reboot therefore needs manual action.
10. **Stopping relies on `pgrep -f calendarApiServer.py` plus kill.** This is fragile and not needed once systemd owns the process.
11. **Permissions:** the private key is copied with `mode: u=rwx` (0700). Restaurants uses `0600`. `credentials.json` and `token.json` are not locked down.
12. **Log directory mismatch:** the playbook creates `/home/pi/logs`, but the app and the background runner write to `app/logs/`. That directory is wiped on each deploy and never recreated.
13. **`become_user: {{ user }}`:** it cannot manage `/etc/systemd/system` or `/etc/credstore.encrypted`, which need root `become`, as in restaurants.
14. **Duplicated tasks:** `windfire-calendar-full-deploy.yaml` copies tasks 1–12 verbatim, so any fix has to be made twice.
15. **Hard-coded values:** `local_home_dir: /Users/robertopozzi` and the wheel version `client-1.0.0` (in `installPrereqs.sh`).

### `raspberry/windfire-calendar-undeploy.yaml`
16. It only kills the process and deletes the directory. There is no systemd or credential cleanup yet, which will be needed once 7 and 9 are fixed.

## Target design

### 1. `deployment/deploy.sh` (keep house style, add the restaurants pre-flight chain)
- `cd "$(dirname "$0")"` at start, then `source ../common.sh`, so the script works from any CWD.
- `main "$@"` everywhere. Add a `-h|--help` branch in `parseArgs` that follows the `printHelp` style of `app/run-apicalendar.sh`.
- Fix `setFunction`: loop until `DEPLOY_PLATFORM` is valid, or exit 1.
- In `deployToRaspberry()`, run these steps in order. Each prints a blue `***** … *****` banner, as `deploy.sh` does in restaurants.
  1. `checkPrerequisites`
     - `ansible-playbook` is on PATH
     - `$HOME/.ssh/ansible_rsa` exists
  2. `checkRootCA`
     - `$WINDFIRE_DEFAULT_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE` exists (variables from `common.sh`)
     - if it is missing, exit and point to `windfire-security/ssl/createRootCA.sh`
  3. `checkSSLCertificates`
     - `windfire-calendar.crt` and `.key` exist in `$WINDFIRE_DEFAULT_CERTS_PROD_DIR`
     - if they are missing, run `(cd ../app/ssl && ./generateServerCert.sh)` and tell the operator to choose **Production**. This mirrors `checkSSLCertificates` in restaurants.
  4. `checkSecurityClientWheel`
     - `../../windfire-security-client/dist/client-*.whl` exists
     - if it is missing, suggest `./createModule.sh` in that repo
  5. `checkAppConfig`
     - `../app/credentials.json` and `../app/token.json` exist
     - if either is missing, explain how to create them by running the app locally once
  6. `collectSecrets` (the restaurants pattern: prompt once, then export). Defaults are read from `../app/.env` with the existing `getEnvFileValue` helper in `common.sh`.
     - `KEYCLOAK_SERVER_HOST`, default `KEYCLOAK_PROD_HOST` (`raspberry01`)
     - `KEYCLOAK_SERVER_PORT`, default `KEYCLOAK_PROD_PORT` (`8444`)
     - `KEYCLOAK_SERVICE`, default from `.env`
     - `KEYCLOAK_CLIENT_SECRET`: reuse `inputKeycloakClientSecret` from `common.sh`, which is silent and non-empty
  7. `runPlaybook`
     - `eval "$(ssh-agent -s)"` followed by `trap 'ssh-agent -k >/dev/null' EXIT`
     - `ssh-add … || exit 1`
     - `ansible-playbook raspberry/windfire-calendar-deploy.yaml`
     - check `$?`, then print a green success message or a red failure message and `exit 1`
- Put new constants in `common.sh`, in the "DEPLOYMENT / UNDEPLOYMENT VARIABLES" section, for example `WINDFIRE_SERVER_CERTIFICATE=windfire-calendar.crt`, `WINDFIRE_SERVER_KEY=windfire-calendar.key` and `SECURITY_CLIENT_DIST_DIR`. Do not hard-code them in `deploy.sh`.

### 2. `deployment/undeploy.sh`
- Apply the same fixes as for `deploy.sh`: CWD, quoting, `setFunction` loop, agent trap, exit-code check, `--help`.
- Ask for confirmation before removing the service (`y/N`), unless `-y` is passed.

### 3. Playbooks (`deployment/raspberry/`)
- **New `tasks/deploy-app.yaml`**: move the shared deploy tasks here. Both `windfire-calendar-deploy.yaml` and `windfire-calendar-full-deploy.yaml` load it with `import_tasks`, and full-deploy keeps only its apt `pre_tasks`. This removes the duplication (finding 14).
- Play header: `become: yes` with no `become_user`, as in restaurants. Tasks that create user-owned files set `owner/group: {{ user }}`.
- Add to the play `vars`: `lookup('env', …)` for `KEYCLOAK_SERVER_HOST`, `KEYCLOAK_SERVER_PORT`, `KEYCLOAK_SERVICE` and `KEYCLOAK_CLIENT_SECRET`.
- Task flow:
  1. **Stop the existing service**
     - `ansible.builtin.systemd: name=windfire-calendar state=stopped`, with `failed_when: false`
     - keep the existing `pgrep` / `kill -TERM` tasks as a **fallback** for processes that were started by hand before this change. They can be dropped once every host has migrated.
  2. **Recreate the application directory**
     - remove and recreate `{{ remote_windfire_calendar_dir }}`
     - create `{{ remote_windfire_calendar_dir }}/app/logs` (fixes finding 12)
  3. **Sync `app/`**
     - keep the existing excludes and add `--exclude=.env`, `--exclude=logs`, `--exclude=token.json` and `--exclude=credentials.json`
     - the local `.env` is replaced by a template (step 4), and the Google files are copied in step 5
  4. **Template `app/.env`** from `templates/windfire-calendar.env.j2`, mode `0600`. Values come from `config.yaml`:
     - `APP_NAME`, `API_HOST=0.0.0.0`, `API_PORT`, `API_PORT_SECURE`
     - `SSL_KEYFILE=./ssl/{{ windfire_server_key }}` and `SSL_CERTFILE=./ssl/{{ windfire_server_certificate }}`
     - `ENFORCE_HTTPS=true`, `ALLOWED_HOSTS={{ allowed_hosts }}`
     - `KEYCLOAK_PROD_HOST/PORT`, `KEYCLOAK_SERVICE`, `DEFAULT_LOG_*`, `GOOGLE_*`

     Only non-secret values go in this file.
  5. **Copy the Google files and TLS material**
     - copy `credentials.json` and `token.json` with mode `0600`
     - copy the cert (`0644`) and the key (**`0600`**) into `app/ssl`, and the Root CA into `remote_truststore_dir`

     This is the existing logic with the permissions tightened (finding 11).
  6. **Copy `common.sh`** (unchanged).
  7. **Security-client wheel, venv, `installPrereqs.sh {{ env }}`, and the pip list** (unchanged).
  8. **Secrets with systemd-creds** (copied from restaurants)
     - build a `set_fact` blob `KEYCLOAK_CLIENT_SECRET=…`, with `no_log: true`
     - ensure `/etc/credstore.encrypted` exists with mode `0700`, owned by root
     - run `systemd-creds encrypt --name=windfire-calendar-secrets --with-key=host - /etc/credstore.encrypted/windfire-calendar-secrets`, with `no_log: true`
  9. **systemd unit** from `templates/windfire-calendar.service.j2`, written to `/etc/systemd/system/windfire-calendar.service`, with a `notify: reload systemd` handler:
     ```ini
     [Unit]
     Description=Windfire Calendar Service API
     After=network-online.target
     Wants=network-online.target

     [Service]
     Type=simple
     User={{ user }}
     WorkingDirectory={{ remote_windfire_calendar_dir }}/app
     Environment=ENVIRONMENT=prod
     Environment=KEYCLOAK_ENVIRONMENT=prod
     Environment=KEYCLOAK_SERVER_HOST={{ keycloak_server_host }}
     Environment=KEYCLOAK_SERVER_PORT={{ keycloak_server_port }}
     Environment=VERIFY_SSL_CERTS=true
     Environment=ROOT_CA_PATH={{ remote_truststore_dir }}/{{ windfire_ca_root_certificate }}
     Environment=LOG_LEVEL={{ log_level }}
     LoadCredentialEncrypted=windfire-calendar-secrets:/etc/credstore.encrypted/windfire-calendar-secrets
     ExecStart=/bin/bash -c 'set -a; source "$CREDENTIALS_DIRECTORY/windfire-calendar-secrets"; set +a; exec {{ venv_path }}/bin/python calendarApiServer.py'
     Restart=on-failure
     RestartSec=5
     StandardOutput=append:{{ remote_windfire_calendar_dir }}/app/logs/windfire-calendar.log
     StandardError=append:{{ remote_windfire_calendar_dir }}/app/logs/windfire-calendar.log

     [Install]
     WantedBy=multi-user.target
     ```
     These are the same env vars that `run-apicalendar.sh` exports today. `load_dotenv()` reads `.env` from `WorkingDirectory`.
  10. **Start the service**: `systemd: daemon_reload=yes name=windfire-calendar state=started enabled=yes`.
  11. **Health check** (restaurants' `wait_for`, plus an app-level probe)
      - `wait_for: port={{ api_port_secure }} host=127.0.0.1 timeout=30`
      - `uri: url=https://{{ health_check_host }}:{{ api_port_secure }}/v1/monitor/health`, with `ca_path` set to the remote Root CA and `status_code: 200`
      - `health_check_host` defaults to `raspberry02`. It must match the cert SAN and be listed in `ALLOWED_HOSTS`.
      - on failure, dump `journalctl -u windfire-calendar -n 50` for diagnosis
- **`conf/config.yaml`**
  - add `service_name: windfire-calendar`, `api_port: 8000`, `api_port_secure: 8443`, `allowed_hosts: raspberry02,localhost`, `health_check_host: raspberry02` and `log_level: INFO`
  - replace `local_home_dir: /Users/robertopozzi` with `"{{ lookup('env', 'HOME') }}"` (finding 15)
  - leave `process` / `run_server_script` in place for the pgrep fallback

### 4. `windfire-calendar-undeploy.yaml` (restaurants uninstall pattern)
- Stop and disable `windfire-calendar` with `ignore_errors: yes`, and keep the pgrep fallback.
- Remove `/etc/systemd/system/windfire-calendar.service` and `/etc/credstore.encrypted/windfire-calendar-secrets`, then run `daemon_reload`.
- Remove `{{ remote_windfire_calendar_dir }}` as today. Leave the shared Root CA, the `dist/` wheel and `/home/pi/logs` in place.
- Set `become: yes` with no `become_user`.

### 5. Keep the local run scripts
`app/run-apicalendar*.sh` and `stop-apicalendar.sh` stay as they are for local dev and test. On the Pi, operators use `sudo systemctl {status|restart|stop} windfire-calendar`.

### 6. Documentation – `README.md` § "Deploy to Raspberry Pi"
Rewrite this section in the restaurants style:
- a numbered list of what `deploy.sh` does (pre-flight → secrets → playbook → systemd → health check)
- a list of what the operator must prepare
- the systemd operations commands, and where the logs are
- the new `undeploy` behavior
- remove the "The playbook does not start the service" paragraph

## Critical files
| File | Change |
|---|---|
| `deployment/deploy.sh` | fixes, pre-flight chain, `collectSecrets`, trap, exit codes, `--help` |
| `deployment/undeploy.sh` | fixes, confirmation prompt |
| `common.sh` | new deployment constants (reuse `getEnvFileValue`, `inputKeycloakClientSecret`) |
| `deployment/raspberry/windfire-calendar-deploy.yaml` | systemd, systemd-creds, templated `.env`, permissions, health check |
| `deployment/raspberry/windfire-calendar-full-deploy.yaml` | apt `pre_tasks` + `import_tasks` |
| `deployment/raspberry/tasks/deploy-app.yaml` | **new**, shared tasks |
| `deployment/raspberry/templates/windfire-calendar.service.j2` | **new** |
| `deployment/raspberry/templates/windfire-calendar.env.j2` | **new** |
| `deployment/raspberry/windfire-calendar-undeploy.yaml` | systemd/credential cleanup |
| `deployment/raspberry/conf/config.yaml` | new vars, `$HOME` lookup |
| `README.md` | deploy section rewrite |

Reference implementations to copy from:
- `windfire-restaurants-backend/deploy.sh`: `checkSSLCertificates`, `collectSecrets`
- `windfire-restaurants-backend/deployment/raspberry/windfire-restaurants.yaml`: systemd-creds block, handlers, `wait_for`
- `windfire-restaurants-backend/deployment/raspberry/windfire-restaurants-uninstall.yaml`
- `windfire-restaurants-backend/deployment/raspberry/templates/*.j2`

## Out of scope / follow-ups
- `windfire-security` has the same gaps (same `deploy.sh` code, no systemd). Apply the same changes there afterwards so that all three repos stay aligned.
- `installPrereqs.sh` hard-codes the wheel name `client-1.0.0-py3-none-any.whl`. A later change could install the newest `$HOME/dist/client-*.whl` instead.
- The Google `token.json` is refreshed on the Pi and overwritten by each deploy with the local copy. That is acceptable for now; the alternative is to copy it only when it is missing on the Pi (`force: no`).

## Verification
1. **Static checks**
   - `bash -n deployment/*.sh` and `shellcheck deployment/*.sh common.sh`
   - `ansible-playbook --syntax-check` on the deploy, full-deploy and undeploy playbooks
   - `ansible-lint deployment/raspberry/`
2. **Dry run**: `ansible-playbook raspberry/windfire-calendar-deploy.yaml --check --diff`, with the env vars exported by hand.
3. **Pre-flight negative tests**: temporarily rename the cert, the wheel and `credentials.json`, then run `./deploy.sh 1`. Each should stop early with a clear red message and exit code ≠ 0. Running from the repo root (`deployment/deploy.sh 1`) should also work.
4. **Full deploy**: `cd deployment && ./deploy.sh 1`. Expect a green success message, and on the Pi:
   - `systemctl status windfire-calendar` is active and enabled
   - `ls -l /etc/credstore.encrypted/` shows the encrypted secret
   - `grep -r KEYCLOAK_CLIENT_SECRET /home/pi/windfire-calendar` finds no plaintext secret
   - `stat` shows mode `0600` on the key, `.env` and `token.json`
5. **Functional check**: from the Mac, run `cd test && ./run-test.sh -e 3 -s 3`. All tests should report PASS.
6. **Resilience**: `sudo kill -9 <pid>` on the Pi, then check that systemd restarts the service within about 5 s. `sudo reboot`, then check that the service comes back without manual action.
7. **Redeploy (idempotency)**: run `./deploy.sh 1` a second time. It should succeed, and the service should restart cleanly.
8. **Undeploy**: `./undeploy.sh 1`. Afterwards the unit, the credential and the app directory are gone, and `systemctl status windfire-calendar` reports "could not be found".
