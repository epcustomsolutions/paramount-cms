#!/usr/bin/env bash
#
# Creates a full Postgres backup of the Paramount CMS database.
# Output is written to backups/paramount-YYYYMMDD-HHMM.dump (compressed,
# binary-safe, restorable with pg_restore). See scripts/README.md for the
# full backup/restore workflow.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
BACKUPS_DIR="$REPO_ROOT/backups"

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "error: pg_dump is not installed." >&2
  echo "  Install on macOS:  brew install libpq && brew link --force libpq" >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "error: .env not found at $ENV_FILE" >&2
  exit 1
fi

DATABASE_URL=$(grep -E '^DATABASE_URL=' "$ENV_FILE" | head -1 | cut -d '=' -f 2-)
if [ -z "${DATABASE_URL:-}" ]; then
  echo "error: DATABASE_URL not set in $ENV_FILE" >&2
  exit 1
fi

# pg_dump needs a direct (non-pooled) connection. Neon's -pooler endpoint
# routes through PgBouncer in transaction mode, which breaks the
# session-level state pg_dump relies on (prepared statements, table locks).
DIRECT_URL="${DATABASE_URL/-pooler/}"

mkdir -p "$BACKUPS_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M)
OUTPUT_FILE="$BACKUPS_DIR/paramount-${TIMESTAMP}.dump"

echo "Dumping database..."
echo "  Output: $OUTPUT_FILE"
echo ""

pg_dump \
  "$DIRECT_URL" \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="$OUTPUT_FILE"

if [ ! -s "$OUTPUT_FILE" ]; then
  echo "error: backup file is empty. Something went wrong." >&2
  exit 1
fi

SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')

echo "Verifying backup integrity..."
# pg_restore --list reads the archive's table of contents without writing
# anything. If the file is corrupt this will fail.
TABLE_COUNT=$(pg_restore --list "$OUTPUT_FILE" | grep -c 'TABLE DATA' || true)

if [ "$TABLE_COUNT" -lt 1 ]; then
  echo "warning: backup contains no table data. Check the dump output." >&2
  exit 1
fi

echo ""
echo "Backup complete."
echo "  File:   $OUTPUT_FILE"
echo "  Size:   $SIZE"
echo "  Tables: $TABLE_COUNT"
echo ""
echo "Next: move this file to offsite storage (iCloud / Dropbox / etc)."
