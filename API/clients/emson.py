from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from API.clients.eminfra.EMInfraDomain import BaseDataclass
from API.auth.enums import AuthType, Environment
from API.auth.factory import RequesterFactory


@dataclass
class Query(BaseDataclass):
    """DTO for EMSON cursor-based search endpoints."""

    size: int
    filters: dict
    orderByProperty: str | None = None
    orderByDirection: str | None = None
    fromCursor: str | None = None
    crs: str | None = "3812"  # Default to Belgian Lambert 2008

    def __dict_factory_override__(self):
        return {
            k: (v.value if isinstance(v, Enum) else v)
            for k, v in ((f, getattr(self, f)) for f in self.__dataclass_fields__)
            if v is not None
        }


class EMSONClient:
    def __init__(
        self,
        auth_type: AuthType = None,
        env: Environment = None,
        settings_path: Path | None = None,
        cookie: str | None = None,
        authenticator=None,
        **kwargs,
    ):
        if authenticator is not None:
            self.requester = authenticator.create_requester()
        else:
            if auth_type is None:
                auth_type = kwargs.get("auth")
            if env is None:
                env = kwargs.get("environment")
            self.requester = RequesterFactory.create_requester(
                auth_type=auth_type, env=env, settings_path=settings_path, cookie=cookie, **kwargs
            )
        self.requester.first_part_url += "emson/"

    def test_connection(self) -> dict[str, Any]:
        return self.requester.get("api/otl/assetrelaties").json()

    def get_resource_by_cursor(
        self,
        resource: str,
        cursor: Optional[str] = None,
        page_size: int = 100,
        filters: Optional[dict] = None,
        order_by_property: Optional[str] = None,
        order_by_direction: Optional[str] = None,
    ) -> Generator[tuple[Optional[str], list[dict[str, Any]]], None, None]:
        query = Query(
            filters=filters or {},
            size=page_size,
            fromCursor=cursor,
            orderByProperty=order_by_property,
            orderByDirection=order_by_direction,
        )
        while True:
            response = self.requester.post(url=f"api/otl/{resource}/search", data=query.json())
            if response.status_code != 200:
                raise ProcessLookupError(
                    f"EMSON request failed ({response.status_code}) for resource '{resource}': "
                    f"{response.content.decode('utf-8')}"
                )
            data = response.json().get("@graph", [])
            cursor = response.headers.get("em-paging-next-cursor")
            if not data:
                yield None, []
                break
            yield cursor, data
            if cursor is None:
                break
            query.fromCursor = cursor

    def get_asset_by_uuid(self, uuid: str) -> dict[str, Any]:
        response = self.requester.get(url=f"api/otl/assets/{uuid}")
        if response.status_code != 200:
            raise ProcessLookupError(
                f"EMSON request failed ({response.status_code}) for asset '{uuid}': {response.content.decode('utf-8')}"
            )
        return response.json()

    def get_assetrelatie_by_uuid(self, uuid: str) -> dict[str, Any]:
        response = self.requester.get(url=f"api/otl/assetrelaties/{uuid}")
        if response.status_code != 200:
            raise ProcessLookupError(
                f"EMSON request failed ({response.status_code}) for assetrelatie '{uuid}': "
                f"{response.content.decode('utf-8')}"
            )
        return response.json()

    def get_assets_by_filter(
        self,
        filter: dict,
        size: int = 100,
        order_by_property: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        yield from (
            item
            for _, items in self.get_resource_by_cursor(
                "assets",
                page_size=size,
                filters=filter,
                order_by_property=order_by_property,
            )
            for item in items
        )

    def get_assetrelaties_by_filter(
        self,
        filter: dict,
        size: int = 100,
        order_by_property: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        yield from (
            item
            for _, items in self.get_resource_by_cursor(
                "assetrelaties",
                page_size=size,
                filters=filter,
                order_by_property=order_by_property,
            )
            for item in items
        )
