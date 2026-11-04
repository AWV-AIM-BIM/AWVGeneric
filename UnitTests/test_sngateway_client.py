from API.clients.sngateway import SNGatewayClient
from UnitTests.helpers.mock_requester import MockRequester, MockResponse


def test_sngateway_get_all_asset_filters():
    requester = MockRequester(
        {"GET:rest/eminfra/asset-filter": MockResponse(status_code=200, json_data=[{"id": "1", "uri": "x", "enabled": True}])}
    )
    client = SNGatewayClient.__new__(SNGatewayClient)
    client.requester = requester
    res = client.get_all_asset_filters()
    assert res[0]["id"] == "1"


def test_sngateway_add_new_asset_filter():
    requester = MockRequester(
        {"POST:rest/eminfra/asset-filter": MockResponse(status_code=200, json_data={"id": "2"})}
    )
    client = SNGatewayClient.__new__(SNGatewayClient)
    client.requester = requester
    res = client.add_new_asset_filter("uri", enabled=True)
    assert res["id"] == "2"


def test_sngateway_enable_existing():
    requester = MockRequester(
        {"GET:rest/eminfra/asset-filter": MockResponse(status_code=200, json_data=[{"id": "1", "uri": "x", "enabled": False}])},
    )
    # For put
    req = requester
    client = SNGatewayClient.__new__(SNGatewayClient)
    client.requester = req
    # Add put response
    req.responses["PUT:rest/eminfra/asset-filter/1"] = MockResponse(status_code=200, json_data={"ok": True})
    client.enable_asset_filter("x")
    assert ("PUT", "rest/eminfra/asset-filter/1") in [(c[0], c[1]) for c in req.calls]
