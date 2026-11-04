from API.auth.settings import find_settings_file, load_settings, resolve_settings_path
from pathlib import Path
import tempfile
import os


def test_find_settings_file_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = find_settings_file("nonexistent_settings_xyz.json")
    assert result is None


def test_resolve_settings_path_absolute():
    p = resolve_settings_path("/etc/hosts")
    assert p.is_absolute()


def test_resolve_settings_path_relative_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = resolve_settings_path("file.txt")
    assert isinstance(p, Path)
