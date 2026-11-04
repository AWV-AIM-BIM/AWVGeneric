from API.clients.eminfra import paging
from API.clients.eminfra.EMInfraDomain import AssetDTO


class DummyResp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class DummyReq:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    def get(self, url=""):
        resp = self.responses[self.calls]
        self.calls += 1
        return resp


def test_offset_page_generator_get_raw():
    req = DummyReq(
        [
            DummyResp({"data": [{"id": 1}], "totalCount": 2, "from": 0}),
            DummyResp({"data": [{"id": 2}], "totalCount": 2, "from": 1}),
        ]
    )
    pages = list(paging.offset_page_generator_get(req, "core", "assets", page_size=1))
    assert len(pages) == 2
    assert pages[0][1] == [{"id": 1}]
    assert pages[1][1] == [{"id": 2}]


def test_offset_page_generator_get_with_dto():
    # Use AssetDTO-like minimal - but easier to just pass a simple dto
    class SimpleDTO:
        def __init__(self, x):
            self.x = x

        @classmethod
        def from_dict(cls, d):
            return cls(d["x"])

    req = DummyReq(
        [
            DummyResp({"data": [{"x": 1}], "totalCount": 1, "from": 0}),
        ]
    )
    pages = list(paging.offset_page_generator_get(req, "core", "assets", page_size=10, dto_type=SimpleDTO))
    assert pages[0][1][0].x == 1
