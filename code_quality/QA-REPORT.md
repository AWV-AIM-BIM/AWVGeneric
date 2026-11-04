# QA Report — awvgeneric

> GENERATED FILE — produced by `code_quality/scripts/qa_report.py`.
> Do not edit by hand; edit the thresholds in the script instead.

Generated: 2026-11-04 · commit `b4d037f`

## Thresholds (gate)

| Metric | Threshold | Current | Status |
|---|---|---|---|
| ruff issues | ≤ 0 | 339 | 🔴 |
| files needing `ruff format` | ≤ 0 | 6 | 🔴 |
| mypy errors | ≤ 0 | 482 | 🔴 |
| test coverage (lines, owned code) | ≥ 80.0 | 33.2 % | 🔴 |
| test coverage (branches, owned code) | ≥ 75.0 | 3.4 % | 🔴 |
| max CRAP score | ≤ 6.0 | 282.6 | 🔴 |
| max cyclomatic complexity | ≤ 6 | 17 | 🔴 |
| bandit HIGH issues | ≤ 0 | 0 | 🟢 |
| dead code items | ≤ 0 | 0 | 🟢 |
| pip-audit vulnerabilities | ≤ 0 | 0 | 🟢 |
| god classes | ≤ 0 | 4 | 🔴 |
| files radon cannot parse | ≤ 0 | 0 | 🟢 |
| manual conventions | ≤ 0 | 0 | 🟢 |
| import cycles/architecture | ≤ — | not enabled | ⚪ |

## Ratchet regressions

These lint counts went **up** compared to the previous cycle and block the merge:

- TRY300: 6 -> 7

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

`API/clients/sharepoint.py:44` → `__init__` — CRAP **282.6** — complexity **17** — coverage **2.8 %**

Verify with `code_quality/README.md` §7 before touching it: the behaviour must be pinned by a golden-file test first.

## Change hot spots (churn x complexity)

| Score | Commits | Lines changed | Max complexity | File |
|---:|---:|---:|---:|---|
| 28373 | 3 | 1669 | 17 | `API/clients/sharepoint.py` |
| 8415 | 3 | 935 | 9 | `API/clients/eminfra/EMInfraDomain.py` |
| 3978 | 2 | 442 | 9 | `API/clients/eminfra/AssetService.py` |
| 2555 | 2 | 365 | 7 | `API/clients/eminfra/BestekService.py` |
| 2200 | 2 | 200 | 11 | `API/clients/eminfra/ToezichterService.py` |

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
| `PLR0913` | 10 |
| `PLR0917` | 10 |
| `F401` | 9 |
| `PTH123` | 9 |
| `S110` | 7 |
| `TRY300` | 7 |
| `F403` | 2 |
| `E712` | 1 |

## History

| Date | Coverage % | Branch % | Ruff | MyPy | Max CRAP | Max complexity | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-11-04 | 33.2 | 3.4 | 0 | 573 | 306.0 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 0 | 573 | 306.0 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 0 | 573 | 306.0 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 0 | 573 | 306.0 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 0 | 573 | 306.0 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 474 | 573 | 306.0 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 338 | 479 | 284.9 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 338 | 479 | 284.9 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 338 | 479 | 284.9 | 17 | red |
| 2026-11-04 | 33.2 | 3.4 | 339 | 482 | 282.6 | 17 | red |
