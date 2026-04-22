# Paramount CMS — Backup & Restore

Operational scripts for backing up and restoring the production Neon Postgres
database. This is the manual weekly-backup workflow for the pilot phase.

## Contents

- `backup.sh` — dump the production DB to a timestamped file in `backups/`.
- `restore.sh` — restore a dump into a Postgres database (with a confirmation
  prompt, because this is destructive).

Both scripts read `DATABASE_URL` from the repo-root `.env` and automatically
switch Neon's pooled endpoint (`...-pooler...`) to the direct endpoint,
because `pg_dump` / `pg_restore` do not work reliably through PgBouncer's
transaction-mode pooler.

## One-time setup

Install the Postgres command-line client tools. On macOS:

```bash
brew install libpq
brew link --force libpq
```

Verify:

```bash
pg_dump --version       # should print pg_dump (PostgreSQL) 17.x or newer
pg_restore --version
```

The major version must be greater than or equal to the Neon server version
(currently 17). If you're on an older `libpq`, upgrade before backing up.

## Taking a backup

From the repo root:

```bash
./scripts/backup.sh
```

The script will:

1. Read `DATABASE_URL` from `.env` and switch to the non-pooled endpoint.
2. Create a `backups/` directory if it doesn't exist (already gitignored).
3. Run `pg_dump` in custom (compressed, binary-safe) format.
4. Verify the resulting file has a valid table-of-contents and at least one
   table of data.
5. Print the file path, size, and table count.

Expected output:

```
Dumping database...
  Output: /Users/epaulz/projects/paramount-cms/backups/paramount-20260422-1620.dump

Verifying backup integrity...

Backup complete.
  File:   /Users/epaulz/projects/paramount-cms/backups/paramount-20260422-1620.dump
  Size:   312K
  Tables: 14

Next: move this file to offsite storage (iCloud / Dropbox / etc).
```

### Cadence

Run this once per week (calendar reminder recommended) while the pilot is
active. If the testers do something high-risk — a bulk import, a mass delete,
anything unusual — take an ad-hoc backup first as well.

### Offsite storage

Having the dump on your laptop only is better than nothing, but not great.
After each backup, move or copy the `.dump` file somewhere that isn't your
laptop:

- **iCloud Drive**, **Dropbox**, or **Google Drive** folder (easiest).
- A private GitHub repo (works fine for files under 100 MB).
- An S3 / R2 / B2 bucket (more involved but cheap).

The contents include every client's name, address, phone, claim details, and
all uploaded documents (PDFs, Word, Excel), so treat the backup file with the
same care you'd give a password manager export.

## Verifying a backup manually

The script already runs a basic integrity check, but if you want to inspect a
dump more carefully:

```bash
# List everything inside the archive (tables, indexes, constraints).
pg_restore --list backups/paramount-YYYYMMDD-HHMM.dump

# How big is the archive?
ls -lh backups/paramount-*.dump
```

A healthy backup will contain `TABLE DATA` entries for each app:
`auth_user`, `clients_client`, `claims_claim`, `claims_claimnote`,
`claims_claimdocument`, `scheduling_appointment`, etc.

If you ever want extra confidence before the pilot starts, do a full
dry-run restore into a throwaway Neon branch (see below) and log in to
verify the data looks right.

## Restoring a backup

Restore is destructive — it drops and recreates every table in the target
database. There are two common scenarios:

### Scenario 1 — "Something went wrong, restore over production"

Typical trigger: a tester did something catastrophic more than 6 hours ago
(outside Neon's free-tier PITR window), and the last good state is in a
recent backup.

```bash
./scripts/restore.sh backups/paramount-YYYYMMDD-HHMM.dump
```

The script will:

1. Read `DATABASE_URL` from `.env`, switch to the non-pooled endpoint.
2. Display the source file and masked target URL.
3. Wait for you to type the word `restore` to confirm.
4. Run `pg_restore` with `--clean --if-exists`, which drops existing tables
   before recreating them.

**Before running this**, strongly consider the safer alternative below first.

### Scenario 2 — "Restore into a fresh Neon branch, verify, then swap" (safer)

Rather than overwriting production directly, restore into an isolated Neon
branch, verify the restored data, and only then point the app at it. This
lets you abort with zero downtime if the restored backup turns out to be
wrong or incomplete.

Steps:

1. In the Neon console, create a new branch from the current primary (e.g.
   `restore-2026-04-22`). This gives you a fresh empty database with its own
   connection URL.
2. Copy the new branch's connection string.
3. Run restore with the explicit target URL override:

   ```bash
   ./scripts/restore.sh backups/paramount-YYYYMMDD-HHMM.dump \
     "postgresql://USER:PASS@NEW-BRANCH-HOST/neondb?sslmode=require"
   ```

   (Pass the direct endpoint — without `-pooler` — just like the backup
   script does automatically.)
4. Point a local Django at the restored branch, log in, spot-check the data.
5. If everything looks right, update `DATABASE_URL` in the Vercel
   environment variables to the restored branch's **pooled** URL (with
   `-pooler`), and redeploy. Keep the old branch around for a week in case
   of buyer's remorse.

This path is slower (~15 extra minutes) but eliminates the "what if the
backup was corrupt and now both production and my recovery attempt are
broken?" failure mode.

### After a restore

Two things worth doing, regardless of path:

- `python manage.py showmigrations` against the restored DB to confirm the
  migration state matches what your current code expects.
- A quick `python manage.py migrate --check` to catch any schema drift.

If the backup was taken with an older migration state than your current
code, run `python manage.py migrate` to catch up.

## Troubleshooting

### `pg_dump: server version mismatch`

Your local `libpq` is older than Neon's server. Upgrade Homebrew's `libpq`:

```bash
brew upgrade libpq
brew link --force libpq
```

### `pg_dump: connection to server failed: ... prepared statement "..." already exists`

You're connecting through the pooled endpoint. The scripts auto-strip
`-pooler`, so if you see this you're probably running `pg_dump` manually
with the pooled URL from `.env`. Strip `-pooler` from the hostname.

### `channel_binding` errors

Some `libpq` builds don't support `channel_binding=require`. If a manual
`pg_dump` call fails citing channel binding, remove that query parameter
from the URL. It's safety-in-depth, not a security requirement.

### Backup file is suspiciously small

Look at the output table count from the script. If it's fewer than ~10, the
dump may have run against an empty branch or stopped mid-way. Re-run and
watch the output for errors.

### Something weird — restore errored midway

`pg_restore` with `--clean --if-exists` is usually idempotent and safe to
re-run. If it keeps erroring, capture the output and check:

- Target DB must have no active connections holding locks on tables being
  dropped. Restart the app, or on Neon kill the branch's active sessions.
- Extensions — if the dump uses any Postgres extensions not installed on
  the target (unlikely for this app), add them first with
  `CREATE EXTENSION IF NOT EXISTS <name>`.
