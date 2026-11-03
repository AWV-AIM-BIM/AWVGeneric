"""TypedDict definitions for settings (optional typing only)."""
from typing import TypedDict, Dict


class JWTSettings(TypedDict, total=False):
    key_path: str
    client_id: str


class CertSettings(TypedDict, total=False):
    cert_path: str
    key_path: str


class CookieSettings(TypedDict, total=False):
    cookie: str


class AuthSettings(TypedDict, total=False):
    JWT: Dict[str, JWTSettings]
    CERT: Dict[str, CertSettings]
    COOKIE: Dict[str, CookieSettings]


class AWVSettings(TypedDict, total=False):
    authentication: AuthSettings
