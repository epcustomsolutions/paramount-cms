#!/usr/bin/env bash
#
# Restores a pg_dump archive into a Postgres database.
# WARNING: this DROPS and recreates all tables in the target database.
# Requires explicit confirmation. See scripts/README.md for guidance on
# choosing the target database (fresh branch vs. in-place).
#
# Usage:
#   ./scripts/restore.sh <backup-file> [target-database-url]
#
# If no target URL is provided, DATABASE_URL from .env is used (with the
# -pooler suffix stripped).
#
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "Usage: $0 <backup-file> [target-database-url]" >&2
  exit 1
fi

BACKUP_FILE="$1"
TARGET_URL="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "error: backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "error: pg_restore is not installed." >&2
  echo "  Install on macOS:  brew install libpq && brew link --force libpq" >&2
  exit 1
fi

if [ -z "$TARGET_URL" ]; then
  if [ ! -f "$ENV_FILE" ]; then
    echo "error: no target URL provided and .env not found" >&2
    exit 1
  fi
  DATABASE_URL=$(grep -E '^DATABASE_URL=' "$ENV_FILE" | head -1 | cut -d '=' -f 2-)
  if [ -z "${DATABASE_URL:-}" ]; then
    echo "error: DATABASE_URL not set in $ENV_FILE" >&2
    exit 1
  fi
  TARGET_URL="${DATABASE_URL/-pooler/}"
fi

# Mask password in the confirmation prompt so we don't splash it on screen.
DISPLAY_URL=$(echo "$TARGET_URL" | sed -E 's|://([^:]+):[^@]+@|://\1:***@|')

echo "About to restore:"
echo "  Source: $BACKUP_FILE"
echo "  Target: $DISPLAY_URL"
echo ""
echo "This will DROP and recreate all tables in the target database."
echo "All existing data in the target will be lost."
echo ""
read -r -p "Type 'restore' to proceed: " CONFIRM

if [ "$CONFIRM" != "restore" ]; then
  echo "Aborted."
  exit 1
fi

pg_restore \
  --dbname "$TARGET_URL" \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  --verbose \
  "$BACKUP_FILE"

echo ""
echo "Restore complete."
