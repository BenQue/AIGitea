#!/usr/bin/env sh
set -eu

: "${PGHOST:?PGHOST is required}"
: "${PGPORT:?PGPORT is required}"
: "${PGDATABASE:?PGDATABASE is required}"
: "${PGUSER:?PGUSER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"
: "${MIGRATION_MARKER:?MIGRATION_MARKER is required}"
: "${MIGRATION_HOLD_SECONDS:=0}"

case "$MIGRATION_HOLD_SECONDS" in
  0|1|2|3|4|5) ;;
  *) printf '%s\n' 'MIGRATION_HOLD_SECONDS must be between 0 and 5' >&2; exit 64 ;;
esac

psql --no-psqlrc --set=ON_ERROR_STOP=1 <<'SQL'
CREATE SCHEMA IF NOT EXISTS issue65_fixture;
CREATE TABLE IF NOT EXISTS issue65_fixture.migration_receipt (
  marker text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);
SQL
sleep "$MIGRATION_HOLD_SECONDS"
psql --no-psqlrc --set=ON_ERROR_STOP=1 \
  --set=marker="$MIGRATION_MARKER" <<'SQL'
INSERT INTO issue65_fixture.migration_receipt(marker)
VALUES (:'marker')
ON CONFLICT (marker) DO NOTHING;
SQL
