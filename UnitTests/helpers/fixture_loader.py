import json
from pathlib import Path
from typing import Any


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "eminfra" / "sanitized"


def load_fixture(name: str) -> Any:
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_fixture_raw(filename: str) -> Any:
    path = FIXTURES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
