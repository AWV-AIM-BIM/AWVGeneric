"""AWV API Client Library.

Usage:
    from API import AWVAppAuthenticator
    from API.auth.enums import AuthType, Environment

    auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE)
    client = auth.eminfra()
"""

from API.auth.authenticator import AWVAppAuthenticator

__all__ = ["AWVAppAuthenticator"]