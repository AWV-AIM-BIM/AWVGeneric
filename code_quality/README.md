# Code Quality

Python code-quality bundle for AI agents.

## Start here
- **Run gates:** `python code_quality/scripts/qa_report.py`
- **Find hotspots (CRAP/churn):** `python code_quality/scripts/crap_scores.py --source API --top 25`
- **Port to another repo:** [`PORTING.md`](PORTING.md)
- **Process/gates/ratchet/mypy staging:** [`PROCESS.md`](PROCESS.md)
- **Banned constructs:** [`PY-ANTI-PATTERNS.md`](PY-ANTI-PATTERNS.md)
- **Manual conventions:** [`MANUAL-CONVENTIONS.md`](MANUAL-CONVENTIONS.md)
- **Repo-specific baseline (this repo):** [`AWV-BASELINE.md`](AWV-BASELINE.md)

## Scope

Only the `API/` package is in scope for this bundle. The rest of the repository
(`UseCases/`, `utils/`, `UnitTests/`, the notebooks and the ad-hoc scripts at the
root) is not part of the vendored API library and is excluded from the quality
gate. The test directory (`UnitTests/`) is linted and type-checked, but it is not
part of the coverage gate.

## Files
| Path | What it is |
|---|---|
| `scripts/qa_report.py` | Runs all gates, writes `QA-REPORT.md` + `reports/qa.json`, updates history |
| `scripts/crap_scores.py` | CRAP ranking + change hot spots |
| `coverage.cfg` | Coverage config for quality gate |
| `ci/quality.yml` | GitHub Actions template (copy to `.github/workflows/quality.yml`) |
| `reports/` | Generated artifacts (never edit by hand) |
| `QA-REPORT.md` | Generated dashboard (never edit by hand) |