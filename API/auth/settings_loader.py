import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_settings(settings_path: Optional[str] = None) -> Dict[str, Any]:
    """Load settings from a JSON file.

    Default is ./settings.json. You should not commit this file.
    Commit ./settings.example.json instead.
    """
    path = Path(settings_path or "settings.json")
    if not path.exists():
        raise FileNotFoundError(
            f"Missing settings file: {path.resolve()}\n"
            "Create settings.json (not committed) based on settings.example.json."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_auth_config(settings: dict, auth_type_name: str, env_name: str) -> dict:
    """Get authentication configuration for specific auth type and environment."""
    return settings['authentication'][auth_type_name][env_name.lower()]
