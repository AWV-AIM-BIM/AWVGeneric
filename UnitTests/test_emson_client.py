from API.clients.emson import EMSONClient
from UnitTests.helpers.mock_requester import MockRequester, MockResponse


def test_emson_client_init_with_mock():
    client = EMSONClient.__new__(EMSONClient)
    requester = MockRequester()
    client.requester = requester
    client.requester.first_part_url = ""
    assert client.requester is requester


def test_emson_test_connection():
    requester = MockRequester(
        {"GET:api/otl/assetrelaties": MockResponse(status_code=200, json_data={"@graph": []})}
    )
    client = EMSONClient.__new__(EMSONClient)
    client.requester = requester
    res = client.test_connection()
    assert res == {"@graph": []}


def test_emson_get_asset_by_uuid():
    requester = MockRequester(
        {
            "GET:api/otl/assets/00000000-0000-0000-0000-000000000001": MockResponse(
                status_code=200,
                json_data={"@id": "asset/00000000-0000-0000-0000-000000000001", "naam": "Test"},
            )
        }
    )
    client = EMSONClient.__new__(EMSONClient)
    client.requester = requester
    res = client.get_asset_by_uuid("00000000-0000-0000-0000-000000000001")
    assert res["naam"] == "Test"


def test_emson_get_assetrelatie_by_uuid():
    requester = MockRequester(
        {
            "GET:api/otl/assetrelaties/11111111-1111-1111-1111-111111111111": MockResponse(
                status_code=200,
                json_data={"@id": "assetrelatie/11111111-1111-1111-1111-111111111111"},
            )
        }
    )
    client = EMSONClient.__new__(EMSONClient)
    client.requester = requester
    res = client.get_assetrelatie_by_uuid("11111111-1111-1111-1111-111111111111")
    assert res["@id"] is not None


def test_emson_get_assets_by_filter():
    requester = MockRequester(
        {"POST:api/otl/assets/search": MockResponse(status_code=200, json_data={"@graph": [{"@id": "asset/1", "naam": "A"}]})}
    )
    requester.responses["POST:api/otl/assets/search"].headers = {"em-paging-next-cursor": None}

    client = EMSONClient.__new__(EMSONClient)
    client.requester = requester
    results = list(client.get_assets_by_filter({"typeUri": "x"}))
    assert len(results) == 1
    assert results[0]["naam"] == "A"


def test_emson_get_assetrelaties_by_filter():
    requester = MockRequester(
        {"POST:api/otl/assetrelaties/search": MockResponse(status_code=200, json_data={"@graph": [{"@id": "rel/1"}]})}
    )
    requester.responses["POST:api/otl/assetrelaties/search"].headers = {"em-paging-next-cursor": None}

    client = EMSONClient.__new__(EMSONClient)
    client.requester = requester
    results = list(client.get_assetrelaties_by_filter({"asset": "x"}))
    assert len(results) == 1


def test_emson_get_resource_by_cursor_pagination():
    class R1:
        status_code = 200

        def json(self):
            return {"@graph": [{"id": 1}]}

        headers = {"em-paging-next-cursor": "abc123"}
        content = b"{}"

    class R2:
        status_code = 200

        def json(self):
            return {"@graph": [{"id": 2}]}

        headers = {"em-paging-next-cursor": None}
        content = b"{}"

    class Req:
        def __init__(self):
            self.calls = 0
            self.first_part_url = ""

        def post(self, url="", **kwargs):
            self.calls += 1
            if self.calls == 1:
                return R1()
            return R2()

    client = EMSONClient.__new__(EMSONClient)
    client.requester = Req()
    pages = list(client.get_resource_by_cursor("assets"))
    assert len(pages) == 2
    assert pages[0][0] == "abc123"
    assert pages[1][0] is None
