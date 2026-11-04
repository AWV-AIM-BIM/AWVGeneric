from API.auth.cookie import CookieRequester


def test_cookie_requester_init():
    r = CookieRequester(cookie="testcookie", first_part_url="https://example.com/")
    assert r.cookie == "testcookie"
    assert "Cookie" in r.headers


def test_cookie_requester_modify_kwargs():
    kwargs = {}
    res = CookieRequester.modify_kwargs_for_bearer_token(kwargs)
    assert "headers" in res
    assert res["headers"]["Content-Type"] == "application/vnd.awv.eminfra.v1+json"
