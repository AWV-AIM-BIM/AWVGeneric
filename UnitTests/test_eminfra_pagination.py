from API.clients.eminfra.AssetService import AssetService
from API.clients.eminfra.EventService import EventService
from API.clients.eminfra.EMInfraDomain import (
    QueryDTO,
    PagingModeEnum,
    SelectionDTO,
    ExpressionDTO,
    TermDTO,
    OperatorEnum,
)


def make_asset_dict(uuid):
    return {
        "_type": "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Test",
        "uuid": uuid,
        "createdOn": "2020-01-01T00:00:00",
        "modifiedOn": "2020-01-01T00:00:00",
        "naam": f"TestAsset-{uuid}",
        "actief": True,
        "links": [],
        "toestand": "IN_GEBRUIK",
    }


def test_asset_service_search_assets_generator_multi_page():
    class R1:
        status_code = 200

        def json(self):
            return {
                "data": [make_asset_dict("00000000-0000-0000-0000-000000000001")],
                "totalCount": 2,
                "from": 0,
            }

        content = b"{}"

    class R2:
        status_code = 200

        def json(self):
            return {
                "data": [make_asset_dict("00000000-0000-0000-0000-000000000002")],
                "totalCount": 2,
                "from": 1,
            }

        content = b"{}"

    calls = 0

    class Req:
        def __init__(self):
            self.first_part_url = ""

        def post(self, url="", **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return R1()
            return R2()

    service = AssetService(Req())
    query_dto = QueryDTO(
        size=1,
        from_=0,
        pagingMode=PagingModeEnum.OFFSET,
        selection=SelectionDTO(expressions=[ExpressionDTO(terms=[TermDTO(property="naam", operator=OperatorEnum.EQ, value="x")])]),
    )
    results = list(service.search_assets_generator(query_dto))
    assert len(results) == 2


def test_event_service_search_events_by_uuid_generator_multi_page():
    class Ev1:
        status_code = 200

        def json(self):
            return {
                "data": [
                    {
                        "type": {"name": "CREATED", "description": "created"},
                        "eventNumber": 1,
                        "createdOn": "2024-01-01T00:00:00",
                        "determinedOn": "2024-01-01T00:00:00",
                        "data": {},
                        "links": [],
                    }
                ],
                "totalCount": 150,
                "from": 0,
            }

        content = b"{}"

    class Ev2:
        status_code = 200

        def json(self):
            return {
                "data": [
                    {
                        "type": {"name": "UPDATED", "description": "updated"},
                        "eventNumber": 2,
                        "createdOn": "2024-01-02T00:00:00",
                        "determinedOn": "2024-01-02T00:00:00",
                        "data": {},
                        "links": [],
                    }
                ],
                "totalCount": 150,
                "from": 100,
            }

        content = b"{}"

    calls = 0

    class Req:
        def __init__(self):
            self.first_part_url = ""

        def post(self, url="", **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return Ev1()
            return Ev2()

    service = EventService(Req())
    results = list(service.search_events_by_uuid_generator("00000000-0000-0000-0000-000000000001"))
    assert len(results) == 2
    assert results[0].eventNumber == 1
    assert results[1].eventNumber == 2
