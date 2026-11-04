# EMInfra Fixtures

## Capture
Use `scripts/capture_fixtures.py` against TEI or DEV (non-prod) environment. Never hit production.

## Sanitize
Run `scripts/sanitize_fixtures.py` to scramble PII, hash/replace names/emails, remap UUIDs consistently. UUID mappings are stored in `mappings/uuid_mapping.json` to preserve referential integrity.

## Usage
Tests load fixtures from `sanitized/` via test helpers. Fixtures are fully offline - no network calls.
