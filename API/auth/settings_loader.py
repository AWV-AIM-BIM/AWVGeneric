"""Settings loader - delegates to auth.settings for backward compatibility."""
from API.auth.settings import load_settings, find_settings_file, resolve_settings_path

__all__ = ['load_settings', 'find_settings_file', 'resolve_settings_path']


def get_auth_config(settings: dict, auth_type_name: str, env_name: str) -> dict:
    """Get authentication configuration for specific auth type and environment."""
    return settings['authentication'][auth_type_name][env_name.lower()]
