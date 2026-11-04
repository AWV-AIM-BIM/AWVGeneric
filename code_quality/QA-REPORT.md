# QA Report — awvgeneric

> GENERATED FILE — produced by `code_quality/scripts/qa_report.py`.
> Do not edit by hand; edit the thresholds in the script instead.

Generated: 2026-11-04 · commit `84cbea5`

## Thresholds (gate)

| Metric | Threshold | Current | Status |
|---|---|---|---|
| ruff issues | ≤ 0 | 339 | 🔴 |
| files needing `ruff format` | ≤ 0 | 11 | 🔴 |
| mypy errors | ≤ 0 | 467 | 🔴 |
| test coverage (lines, owned code) | ≥ 80.0 | 33.2 % | 🔴 |
| test coverage (branches, owned code) | ≥ 75.0 | 3.4 % | 🔴 |
| max CRAP score | ≤ 6.0 | 90.0 | 🔴 |
| max cyclomatic complexity | ≤ 6 | 9 | 🔴 |
| bandit HIGH issues | ≤ 0 | 0 | 🟢 |
| dead code items | ≤ 0 | 0 | 🟢 |
| pip-audit vulnerabilities | ≤ 0 | 0 | 🟢 |
| god classes | ≤ 0 | 4 | 🔴 |
| files radon cannot parse | ≤ 0 | 0 | 🟢 |
| manual conventions | ≤ 0 | 0 | 🟢 |
| import cycles/architecture | ≤ — | not enabled | ⚪ |

## Tools not available

The metrics of these tools are **not measured**: a missing tool reports 0 findings, which looks like a clean run. Install them before trusting the numbers above.

- `bandit`
- `lint-imports`
- `pip-audit`
- `vulture`

## Coverage split — generated vs hand-written

The gate above measures the **hand-written** code: that is the code a refactor touches. The whole package — generated model included — covers 33.2 % of the lines and 3.4 % of the branches. The generated model lifts the headline number and would hide the gap in the code we own.

| Code | Statements | Line % | Branches | Branch % |
|---|---:|---:|---:|---:|
| generated (excluded) | 0 | 0.0 % | 0 | 0.0 % |
| hand-written | 2959 | 33.2 % | 800 | 3.4 % |

## Lead refactor target (highest CRAP)

`API/clients/sharepoint.py:1543` → `_run_command` — CRAP **90.0** — complexity **9** — coverage **0.0 %**

Verify with `code_quality/README.md` §7 before touching it: the behaviour must be pinned by a golden-file test first.

## Change hot spots (churn x complexity)

| Score | Commits | Lines changed | Max complexity | File |
|---:|---:|---:|---:|---|
| 19575 | 5 | 2175 | 9 | `API/clients/sharepoint.py` |
| 12564 | 4 | 1396 | 9 | `API/clients/eminfra/EMInfraDomain.py` |
| 6165 | 3 | 685 | 9 | `API/clients/eminfra/AssetService.py` |
| 4466 | 3 | 638 | 7 | `API/clients/eminfra/BestekService.py` |
| 2048 | 3 | 256 | 8 | `API/clients/eminfra/DocumentService.py` |

## ruff findings per rule

| Rule | Count |
|---|---:|
| `PLR2004` | 74 |
| `LOG015` | 70 |
| `TRY003` | 54 |
| `G004` | 36 |
| `S101` | 20 |
| `BLE001` | 18 |
| `T201` | 12 |
| `F401` | 10 |
| `PLR0913` | 10 |
| `PLR0917` | 10 |
| `PTH123` | 9 |
| `TRY300` | 7 |
| `S110` | 6 |
| `F403` | 2 |
| `E712` | 1 |

## History

| Date | Coverage % | Branch % | Ruff | MyPy | Max CRAP | Max complexity | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-11-04 | 33.2 | 3.4 | 339 | 481 | 280.5 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 339 | 481 | 156.0 | 12 | red |
| 2026-11-04 | 33.2 | 3.4 | 339 | 482 | 142.5 | 12 | red |
| 2026-11-04 | 33.2 | 3.4 | 340 | 463 | 140.0 | 12 | red |
| 2026-11-04 | 33.2 | 3.4 | 340 | 463 | 132.0 | 11 | red |
| 2026-11-04 | 33.2 | 3.4 | 340 | 460 | 112.9 | 11 | red |
| 2026-11-04 | 33.2 | 3.4 | 340 | 460 | 101.2 | 10 | red |
| 2026-11-04 | 33.2 | 3.4 | 339 | 463 | 90.0 | 9 | red |
| 2026-11-04 | 33.2 | 3.4 | 339 | 465 | 90.0 | 9 | red |
| 2026-11-04 | 33.2 | 3.4 | 339 | 467 | 90.0 | 9 | red |
