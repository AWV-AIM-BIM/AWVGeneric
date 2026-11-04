from API.auth.abstract_requester import AbstractRequester
from requests.exceptions import RequestException


class Dummy(AbstractRequester):
    def __init__(self):
        super().__init__(first_part_url="https://example.com/", retries=2)


def test_abstract_requester_init_bad_retries():
    try:
        Dummy.__init__(Dummy())
    except Exception:
        pass


def test_abstract_requester_error_details_json():
    class R:
        def json(self):
            return {"message": "boom"}

    d = AbstractRequester.__new__(AbstractRequester)
    res = d._get_error_details_from_response(R())
    assert res == "boom"


def test_abstract_requester_error_details_none():
    d = AbstractRequester.__new__(AbstractRequester)
    res = d._get_error_details_from_response(None)
    assert res is None
