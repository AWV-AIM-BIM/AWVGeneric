from API.auth.factory import RequesterFactory
from API.auth.enums import AuthType, Environment
from API.auth.authenticator import AWVAppAuthenticator


def test_requester_factory_get_first_part_url():
    url = RequesterFactory._get_first_part_url(Environment.PRD)
    assert url.startswith("https://")


def test_authenticator_methods_exist():
    auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE, cookie="test")
    assert hasattr(auth, "eminfra")
    assert hasattr(auth, "sngateway")
    assert hasattr(auth, "emson")
    assert hasattr(auth, "locatieservices2")
    assert hasattr(auth, "fs")
    assert hasattr(auth, "onedrive")
    assert hasattr(auth, "create_requester")


def test_authenticator_create_requester_cookie():
    auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE, cookie="abc123")
    requester = auth.create_requester()
    assert requester is not None
    assert hasattr(requester, "cookie")
