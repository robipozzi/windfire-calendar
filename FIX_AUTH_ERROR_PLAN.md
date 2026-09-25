# Fix plan: `CERTIFICATE_VERIFY_FAILED` against Keycloak on raspberry01

> Execution note: the only action on approval is to save this document as
> `/Users/robertopozzi/dev/windfire-calendar/FIX_AUTH_ERROR_PLAN.md`. The remediation steps below are **not** to be run now.

## Context

Running `app/run-apicalendar.sh` with Keycloak environment `prod` and then calling a protected API fails with:

```
2026-09-25 16:12:12,816 - ERROR - authClient - Token verification failed: HTTPSConnectionPool(host='raspberry01', port=8444):
... SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate'))
```

### How the two logs line up

| Time | `windfire_calendar.log` | `windfire-security-client.log` | Meaning |
|---|---|---|---|
| 16:00:55 | Server start, `KEYCLOAK_ENVIRONMENT: dev`, host `localhost:8444` | AuthClient initialised, base URL `https://localhost:8444` | Run #1, against dev Keycloak |
| 16:02:50.366 | `commons - Calling client.authClient.verify()` | 16:02:50.388 `Connection refused` | **Separate issue:** no local auth server was listening on `localhost:8444` |
| 16:10:17 | Server start, `KEYCLOAK_ENVIRONMENT: prod`, host `raspberry01:8444` | AuthClient initialised, base URL `https://raspberry01:8444`, CA bundle `~/opt/windfire/ssl/truststore/WindfireRootCA.crt` | Run #2, against prod Keycloak |
| 16:12:12.660 | `commons - Calling client.authClient.verify()` | 16:12:12.816 `CERTIFICATE_VERIFY_FAILED` | **The error being fixed here** |

The configuration is correct: `VERIFY_SSL_CERTS=true` and `ROOT_CA_PATH` points to the Windfire Root CA. The authClient sends `requests.post(..., verify=self.ca_bundle_path)` (`windfire-security-client/client/authClient.py:164-167`). The TLS handshake reaches raspberry01, but the server's certificate does not chain to that CA file.

### Root cause (confirmed with openssl)

The Windfire Root CA was **regenerated** on 2026-08-26 at 15:39 GMT. The new CA kept the same Distinguished Name but has a **new key pair**. The Windfire Security server certificate on raspberry01 was issued about 8 hours **earlier** and was signed by the **old** CA key. It was never re-issued.

| Certificate | Issued (GMT) | Key identifier |
|---|---|---|
| Local Root CA `~/opt/windfire/ssl/truststore/WindfireRootCA.crt` | 2026-08-26 15:39 | Subject Key ID `B8:54:70:9E…0E:8C` |
| raspberry01:8444 live cert (= `~/opt/windfire/ssl/certs/raspberry/windfire-security.crt`) | 2026-08-26 07:55 | Authority Key ID **`08:BD:01:EE…8C:78`** ❌ (does not match) |
| raspberry02 `windfire-cert.pem`, `windfire-restaurants-backend.crt` | 2026-08-26 15:58 / 2026-09-18 | Authority Key ID `B8:54:70:9E…` ✅ (already re-issued) |
| Local calendar cert `app/ssl/windfire-calendar.crt` | – | Authority Key ID `B8:54:70:9E…` ✅ |

`openssl verify -CAfile ~/opt/windfire/ssl/truststore/WindfireRootCA.crt <raspberry01 cert>` returns `error 20: unable to get local issuer certificate`, which is the same error Python reports. Because both CAs have the same subject name, the issuer names look identical. Only the key identifiers show the mismatch.

**Why this is not a calendar-side bug:** no change to `windfire-calendar` code or config is needed. The certificate on the Keycloak/security server has to be re-issued with the current Root CA.

## Remediation (recommended)

Re-issue the Windfire Security server certificate with the current Root CA, then redeploy it to raspberry01. All the tooling already exists in the `windfire-security` repo.

1. **Back up the old cert and key** (optional but advisable):
   `cp ~/opt/windfire/ssl/certs/raspberry/windfire-security.{crt,key} ~/opt/windfire/ssl/certs/raspberry/backup-2026-08-26/`
2. **Generate a new certificate for prod:**
   `cd ~/dev/windfire-security/ssl && ./generateServerCert.sh` and select the **prod** environment.
   - It uses `openssl_config_raspberry.ext` (SAN `DNS:raspberry01`) and writes to `$WINDFIRE_DEFAULT_CERTS_PROD_DIR` = `~/opt/windfire/ssl/certs/raspberry`.
   - It signs with `~/opt/windfire/ssl/truststore/WindfireRootCA.crt` and `~/opt/windfire/ssl/keystore/WindfireRootCA.key` (the current CA).
   - Keep the CN the script proposes. Make sure the SAN still contains `raspberry01`, because `requests` checks the hostname against the SAN.
3. **Check the new cert locally before deploying:**
   ```
   openssl verify -CAfile ~/opt/windfire/ssl/truststore/WindfireRootCA.crt ~/opt/windfire/ssl/certs/raspberry/windfire-security.crt   # expect: OK
   openssl x509 -in ~/opt/windfire/ssl/certs/raspberry/windfire-security.crt -noout -ext authorityKeyIdentifier,subjectAltName          # expect AKI B8:54:70:9E…, DNS:raspberry01
   ```
4. **Redeploy to raspberry01:**
   `cd ~/dev/windfire-security/deployment && ./deploy.sh`
   The Ansible playbook `raspberry/windfire-security-deploy.yaml` stops `authServer.py`. It then copies `windfire-security.crt/.key` (Task 4) and the current `WindfireRootCA.crt` (Task 6) to the Pi, and restarts the service.
5. **Check any other TLS listener on raspberry01.** If port 8444 is served by something other than `authServer.py` (for example a Keycloak instance with its own keystore under `windfire-security/keycloak/security`), that keystore also has to be rebuilt from the new cert. Confirm with the verification step below that the certificate served on 8444 has changed.

### Related issue (not blocking this fix)
- **Run against dev Keycloak (16:02:50):** `Connection refused` on `localhost:8444` means the local windfire-security auth server was not running. Start it (`windfire-security/server/start-auth-server.sh`) before using `--KEYCLOAK_ENV dev`.

### What not to do
- Do not set `VERIFY_SSL_CERTS=false` as a "fix". It turns off server authentication for the token-verification call.
- Do not regenerate the Root CA again. Every other certificate (raspberry02 UI and restaurants backend, the local calendar cert) is already signed by the current CA and would break.

## Verification

1. From the Mac, confirm the certificate served on 8444 now chains to the local CA:
   ```
   echo | openssl s_client -connect raspberry01:8444 -servername raspberry01 \
        -CAfile ~/opt/windfire/ssl/truststore/WindfireRootCA.crt 2>&1 | grep "Verify return code"
   # expect: Verify return code: 0 (ok)
   ```
2. Python-level check, using the same code path as authClient:
   `python3 -c "import requests; print(requests.get('https://raspberry01:8444/v1/monitor/health', verify='$HOME/opt/windfire/ssl/truststore/WindfireRootCA.crt').status_code)"`
3. Restart the calendar API: `cd ~/dev/windfire-calendar/app && ./run-apicalendar.sh 1 --KEYCLOAK_ENV prod --LOG_LEVEL DEBUG`. Then call a protected endpoint with a valid token (or run `test/run-test.sh`). `windfire-security-client.log` should show no `Token verification failed` after the `Calling endpoint https://raspberry01:8444/v1/security/verify` line.
