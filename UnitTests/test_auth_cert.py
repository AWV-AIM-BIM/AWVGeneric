from API.auth.cert import CertRequester


def test_cert_requester_init():
    r = CertRequester(cert_path="/tmp/cert_test.pem", key_path="/tmp/key_test.pem")
    assert r.cert_path == "/tmp/cert_test.pem"


def test_cert_requester_modify_kwargs():
    kwargs = {}
    res = CertRequester.modify_kwargs_for_bearer_token(kwargs)
    assert res["headers"]["Content-Type"] == "application/vnd.awv.eminfra.v1+json"
