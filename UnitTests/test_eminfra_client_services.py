from API.clients.eminfra.AssetService import AssetService
from API.clients.eminfra.EventService import EventService
from API.clients.eminfra.PostitService import PostitService
from API.clients.eminfra.ToezichterService import ToezichterService
from API.clients.eminfra.EMInfraDomain import (
    QueryDTO,
    PagingModeEnum,
    SelectionDTO,
    ExpressionDTO,
    TermDTO,
    OperatorEnum,
)
from UnitTests.helpers.mock_requester import MockRequester, MockResponse


def make_asset_dict(uuid="00000000-0000-0000-0000-000000000001"):
    return {
        "_type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Test",
        "uuid": uuid,
        "createdOn": "2020-01-01T00:00:00",
        "modifiedOn": "2020-01-01T00:00:00",
        "naam": "TestAsset",
        "actief": True,
        "links": [],
        "toestand": "IN_GEBRUIK",
    }


def test_eminfra_client_init_with_mock_requester():
    from API.clients.eminfra.EMInfraClient import EMInfraClient

    client = EMInfraClient.__new__(EMInfraClient)
    requester = MockRequester()
    client.requester = requester
    client.requester.first_part_url = ""
    client.asset_service = AssetService(requester)
    client.event_service = EventService(requester)
    client.postit_service = PostitService(requester)
    client.toezichter_service = ToezichterService(requester)
    assert client.asset_service.requester is requester


def test_asset_service_get_asset_by_uuid_with_mock():
    requester = MockRequester(
        {
            "GET:core/api/assets/00000000-0000-0000-0000-000000000001": MockResponse(
                status_code=200,
                json_data=make_asset_dict(),
            )
        }
    )
    service = AssetService(requester)
    asset = service.get_asset_by_uuid("00000000-0000-0000-0000-000000000001")
    assert asset.uuid == "00000000-0000-0000-0000-000000000001"


def test_asset_service_search_assets_generator_with_mock():
    requester = MockRequester(
        {
            "POST:core/api/assets/search": MockResponse(
                status_code=200,
                json_data={
                    "data": [make_asset_dict()],
                    "totalCount": 1,
                    "from": 0,
                },
            )
        }
    )
    service = AssetService(requester)
    query_dto = QueryDTO(
        size=100,
        from_=0,
        pagingMode=PagingModeEnum.OFFSET,
        selection=SelectionDTO(expressions=[ExpressionDTO(terms=[TermDTO(property="naam", operator=OperatorEnum.EQ, value="TestAsset")])]),
    )
    results = list(service.search_assets_generator(query_dto))
    assert len(results) == 1
    assert results[0].uuid == "00000000-0000-0000-0000-000000000001"


def test_event_service_search_eventcontexts_generator_with_mock():
    requester = MockRequester(
        {
            "POST:core/api/eventcontexts/search": MockResponse(
                status_code=200,
                json_data={
                    "data": [
                        {
                            "uuid": "11111111-1111-1111-1111-111111111111",
                            "omschrijving": "Test context",
                            "links": [],
                        }
                    ],
                    "totalCount": 1,
                    "from": 0,
                },
            )
        }
    )
    service = EventService(requester)
    results = list(service.search_eventcontexts_generator("Test"))
    assert len(results) == 1


def test_postit_service_get_postit_with_mock():
    requester = MockRequester(
        {
            "GET:core/api/assets/00000000-0000-0000-0000-000000000001/postits/22222222-2222-2222-2222-222222222222": MockResponse(
                status_code=200,
                json_data={
                    "bron": "test",
                    "uuid": "22222222-2222-2222-2222-222222222222",
                    "createdOn": "2024-01-01T00:00:00",
                    "modifiedOn": "2024-01-01T00:00:00",
                    "links": [],
                    "startDatum": "2024-01-01T00:00:00",
                    "eindDatum": "2025-01-01T00:00:00",
                    "commentaar": "Test postit",
                },
            )
        }
    )
    service = PostitService(requester)
    postit = service.get_postit("00000000-0000-0000-0000-000000000001", "22222222-2222-2222-2222-222222222222")
    assert postit is not None
    assert postit.commentaar == "Test postit"


def test_toezichter_service_get_toezichter_by_uuid_with_mock():
    requester = MockRequester(
        {
            "GET:core/api/assets/00000000-0000-0000-0000-000000000001/kenmerken/f0166ba2-757c-4cf3-bf71-2e4fdff43fa3": MockResponse(
                status_code=200,
                json_data={
                    "_type": "https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#Toezicht",
                    "type": {},
                    "links": [],
                    "toezichter": None,
                    "toezichtGroep": None,
                },
            )
        }
    )
    service = ToezichterService(requester)
    toez = service.get_toezichter_by_uuid("00000000-0000-0000-0000-000000000001")
    assert toez is not None
