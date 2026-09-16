#!/bin/sh
set -eu
: "${PGHOST:?required}" "${PGPORT:?required}" "${PGUSER:?required}" "${PGDATABASE:?required}"
marker="$(cat /fixture-release)"
psql --no-psqlrc --set=ON_ERROR_STOP=1 --set=marker="$marker" <<'SQL'
CREATE SCHEMA IF NOT EXISTS issue296_fixture;
CREATE TABLE IF NOT EXISTS issue296_fixture.migration_receipt (
  marker text PRIMARY KEY,
  attempts integer NOT NULL DEFAULT 1
);
INSERT INTO issue296_fixture.migration_receipt(marker) VALUES (:'marker')
ON CONFLICT(marker) DO UPDATE SET attempts = issue296_fixture.migration_receipt.attempts + 1;
SQL
