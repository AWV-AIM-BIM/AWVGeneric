"""Settings file finder - looks in standard locations."""
import json
from pathlib import Path
from typing import Optional, Any

from API.auth.types import AWVSettings


def find_settings_file(filename: str = "settings_AWV_applications.json") -> Optional[Path]:
    """
    Find settings file by searching in standard locations:
    1. ./config/<filename> (next to cwd - preferred for vendoring)
    2. ./<filename> (current working directory)
    3. config/<filename> relative to this API package
    4. Parent directories looking for config/<filename>
    5. API/ folder (for examples)
    """
    cwd = Path.cwd()
    
    # Try the requested filename first, then common alternatives
    filenames_to_try = [filename]
    if filename != "settings.json":
        filenames_to_try.append("settings.json")
    if filename != "settings_AWV_applications.json":
        filenames_to_try.append("settings_AWV_applications.json")
    
    for fname in filenames_to_try:
        candidates = [
            cwd / "config" / fname,
            cwd / fname,
            Path(__file__).parent / fname,
            Path(__file__).parent / "config" / fname,
        ]
        
        # Search up from cwd
        for parent in [cwd] + list(cwd.parents)[:5]:
            candidates.append(parent / "config" / fname)
            candidates.append(parent / fname)
        
        for path in candidates:
            if path.exists() and path.is_file():
                return path
    
    return None


def load_settings(filename: str = "settings_AWV_applications.json") -> AWVSettings:
    """Load settings from standard locations."""
    settings_path = find_settings_file(filename)
    if settings_path is None:
        raise FileNotFoundError(
            f"Could not find {filename}. Searched in ./config/, ./, and parent directories.\n"
            f"Create it in a config/ folder next to where you run your code, "
            f"or based on example files in API/ folder."
        )
    with settings_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_settings_path(path_str: str, settings_file_path: Optional[Path] = None) -> Path:
    """Resolve a path from settings relative to settings file location or cwd."""
    path = Path(path_str)
    if path.is_absolute():
        return path
    
    if settings_file_path is not None:
        # Try relative to settings file first
        resolved = (settings_file_path.parent / path).resolve()
        if resolved.exists():
            return resolved
    
    # Fall back to cwd
    resolved = (Path.cwd() / path).resolve()
    return resolved
