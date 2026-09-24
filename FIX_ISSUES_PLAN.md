# Fix Issues Plan

Issues found while updating the README on 2026-09-24. All of them were fixed on the same day except the one below, which needs a decision on how production secrets are provided.

## Deployment copies local secrets without saying so
- **Where:** [windfire-calendar-deploy.yaml](deployment/raspberry/windfire-calendar-deploy.yaml), Task 4 (rsync of `app/`)
- **Problem:** `app/.env`, `app/credentials.json` and `app/token.json` are gitignored but aren't excluded from the rsync, so the deploy ships whatever local copies exist. The production setup therefore depends on the developer's local files: `.env` may contain dev values (for example placeholder SSL paths), and a missing `token.json` means the Google OAuth consent flow would need a browser on the Pi.
- **Fix:** exclude these files from the rsync and copy production versions explicitly, for example with a dedicated task that reads from a local production config folder, or with Ansible Vault for secrets. Update the README deployment section to match.
