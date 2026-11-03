from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

from API.clients.eminfra.EMInfraDomain import BaseDataclass
from API.auth.enums import AuthType, Environment
from API.auth.factory import RequesterFactory


@dataclass
class Query(BaseDataclass):
    size: int
    filters: dict
    orderByProperty: str
    fromCursor: str | None = None


class EMSONClient:
    def __init__(self, auth_type: AuthType = None, env: Environment = None, settings_path: Path = None,
                 cookie: str = None, authenticator=None, **kwargs):
        if authenticator is not None:
            self.requester = authenticator.create_requester()
        else:
            if auth_type is None:
                auth_type = kwargs.get('auth')
            if env is None:
                env = kwargs.get('environment')
            self.requester = RequesterFactory.create_requester(auth_type=auth_type, env=env,
                                                               settings_path=settings_path,
                                                               cookie=cookie, **kwargs)
        self.requester.first_part_url += 'emson/'

    def get_asset_by_uuid(self, uuid: str) -> dict:
        response = self.requester.get(url=f'api/otl/assets/{uuid}')
        if response.status_code != 200:
            print(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        return response.json()

    def get_assets(self) -> Generator[dict]:
        paging_cursor = None
        while True:
            if paging_cursor:
                response = self.requester.get(url=f'api/otl/assets?pagingMode=CURSOR&fromCursor={paging_cursor}')
            else:
                response = self.requester.get(url=f'api/otl/assets?pagingMode=CURSOR')
            if response.status_code != 200:
                print(response)
                raise ProcessLookupError(response.content.decode("utf-8"))
            print('fetched 100 results')
            yield from response.json()['@graph']
            paging_cursor = response.headers.get('em-paging-next-cursor')
            if paging_cursor is None:
                break

    def get_assetrelatie_by_uuid(self, uuid: str) -> dict:
        response = self.requester.get(url=f'api/otl/assetrelaties/{uuid}')
        if response.status_code != 200:
            print(response)
            raise ProcessLookupError(response.content.decode("utf-8"))
        return response.json()

    def get_assets_by_filter(self, filter: dict, size: int = 100, order_by_property: str = None) -> [dict]:
        """See https://apps.mow.vlaanderen.be/emson/docs/#_post_emsonapiotlassetssearch for more details"""
        query = Query(filters=filter, size=size, orderByProperty=order_by_property)
        while True:
            response = self.requester.post(url='api/otl/assets/search', data=query.json())
            if response.status_code != 200:
                print(response)
                raise ProcessLookupError(response.content.decode("utf-8"))
            yield from response.json()['@graph']
            paging_cursor = response.headers.get('em-paging-next-cursor')
            if paging_cursor is None:
                break
            query.fromCursor = paging_cursor

    def get_assetrelaties_by_filter(self, filter: dict, size: int = 100, order_by_property: str = None) -> [dict]:
        query = Query(filters=filter, size=size, orderByProperty=order_by_property)
        while True:
            response = self.requester.post(url='api/otl/assetrelaties/search', data=query.json())
            if response.status_code != 200:
                print(response)
                raise ProcessLookupError(response.content.decode("utf-8"))

            yield from response.json()['@graph']
            paging_cursor = response.headers.get('em-paging-next-cursor')
            if paging_cursor is None:
                break
            query.fromCursor = paging_cursor
