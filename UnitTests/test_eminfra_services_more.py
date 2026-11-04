from API.clients.eminfra.AssetService import AssetService
from API.clients.eminfra.EventService import EventService
from API.clients.eminfra.PostitService import PostitService
from API.clients.eminfra.ToezichterService import ToezichterService
from API.clients.eminfra.BestekService import BestekService
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


def test_bestek_service_get_bestekkoppeling_by_uuid():
    requester = MockRequester(
        {
            "GET:core/api/installaties/00000000-0000-0000-0000-000000000001/kenmerken/ee2e627e-bb79-47aa-956a-ea167d20acbd/bestekken": MockResponse(
                status_code=200,
                json_data={
                    "data": [
                        {
                            "bron": "test",
                            "bestekRef": {
                                "uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                                "type": "bestekref",
                                "actief": True,
                                "links": [],
                                "createdOn": "2020-01-01T00:00:00",
                                "modifiedOn": "2020-01-01T00:00:00",
                                "eDeltaDossiernummer": "MDN/67-5",
                                "eDeltaBesteknummer": "VJV/2020/00001",
                            },
                        }
                    ]
                },
            )
        }
    )
    service = BestekService(requester)
    koppelingen = service.get_bestekkoppeling_by_uuid("00000000-0000-0000-0000-000000000001")
    assert len(koppelingen) == 1


def test_asset_service_update_toestand_by_uuid():
    requester = MockRequester(
        {
            "GET:core/api/assets/00000000-0000-0000-0000-000000000001": MockResponse(
                status_code=200,
                json_data=make_asset_dict(),
            ),
            "PUT:core/api/assets/00000000-0000-0000-0000-000000000001": MockResponse(
                status_code=202,
                json_data={"uuid": "00000000-0000-0000-0000-000000000001"},
            ),
        }
    )
    service = AssetService(requester)
    from API.clients.eminfra.EMInfraDomain import AssetDTOToestand

    res = service.update_toestand_by_uuid("00000000-0000-0000-0000-000000000001", toestand=AssetDTOToestand.IN_OPBOUW)
    assert res is not None


def test_postit_service_add_postit():
    requester = MockRequester(
        {
            "POST:core/api/assets/00000000-0000-0000-0000-000000000001/postits": MockResponse(
                status_code=202,
                json_data={"uuid": "22222222-2222-2222-2222-222222222222"},
            )
        }
    )
    service = PostitService(requester)
    from datetime import datetime

    res = service.add_postit(
        "00000000-0000-0000-0000-000000000001",
        "comment",
        start_datum=datetime(2024, 1, 1),
        eind_datum=datetime(2024, 12, 31),
    )
    assert res is not None


def test_event_service_search_events_by_uuid_generator_empty():
    requester = MockRequester(
        {
            "POST:core/api/events/search": MockResponse(
                status_code=200,
                json_data={"data": [], "totalCount": 0, "from": 0},
            )
        }
    )
    service = EventService(requester)
    results = list(service.search_events_by_uuid_generator("00000000-0000-0000-0000-000000000001"))
    assert results == []
