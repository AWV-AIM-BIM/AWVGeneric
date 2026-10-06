import logging

from API.eminfra.EMInfraDomain import (KenmerkTypeEnum, KenmerkType, PagingModeEnum, SelectionDTO,
                                       ExpressionDTO, TermDTO, QueryDTO, OperatorEnum)
from API.eminfra.KenmerkService import KenmerkService


class VPlanService:
    def __init__(self, requester):
        self.requester = requester

    def get_vplan_kenmerk_uuid(self, asset_uuid: str = None) -> str | None:
        kenmerk_service = KenmerkService(requester=self.requester)
        kenmerk = kenmerk_service.get_kenmerken_by_uuid(
            asset_uuid=asset_uuid,
            naam=KenmerkTypeEnum.VPLAN
        )
        if not kenmerk:
            return None
        if isinstance(kenmerk, list):
            if not kenmerk:
                return None
            kenmerk = kenmerk[0]
        return kenmerk.type.get("uuid")

    def get_vplankoppelingen_by_uuid(self, asset_uuid: str) -> list:
        vplan_kenmerk_uuid = self.get_vplan_kenmerk_uuid(asset_uuid=asset_uuid)
        if not vplan_kenmerk_uuid:
            return []
        url = f'core/api/assets/{asset_uuid}/kenmerken/{vplan_kenmerk_uuid}/vplannen'
        response = self.requester.get(url)
        if response.status_code != 200:
            logging.error(response)
            raise ProcessLookupError(response.content.decode("utf-8"))

        return [item for item in response.json()['data']]

    def get_vplankoppelingen(self, asset) -> list:
        return self.get_vplankoppelingen_by_uuid(asset_uuid=asset.uuid)

    def verwijder_vplankoppelingen_by_uuid(self, asset_uuid: str, vplankoppeling_uuids: list[str]) -> None:
        """
        Verwijder VPlan koppelingen van een asset op basis van de UUID's van de koppelingen.

        :param asset_uuid: Asset UUID
        :type asset_uuid: str
        :param vplankoppeling_uuids: List of VPlan koppeling UUID's to remove
        :type vplankoppeling_uuids: list[str]
        :return: None
        """
        vplan_kenmerk_uuid = self.get_vplan_kenmerk_uuid(asset_uuid=asset_uuid)
        if not vplan_kenmerk_uuid:
            logging.warning(f"VPlan kenmerk not found for asset {asset_uuid}, nothing to remove")
            return

        url = f'core/api/assets/{asset_uuid}/kenmerken/{vplan_kenmerk_uuid}/vplannen/ops/remove'
        payload = {
            "name": "remove",
            "description": None,
            "async": False,
            "uuids": vplankoppeling_uuids
        }
        response = self.requester.put(url=url, json=payload)
        if response.status_code != 202:
            logging.error(response)
            raise ProcessLookupError(response.content.decode("utf-8"))

    def verwijder_vplankoppelingen(self, asset, vplankoppeling_uuids: list[str]) -> None:
        """
        Verwijder VPlan koppelingen van een asset op basis van de UUID's van de koppelingen.

        :param asset: Asset
        :type asset: AssetDTO
        :param vplankoppeling_uuids: List of VPlan koppeling UUID's to remove
        :type vplankoppeling_uuids: list[str]
        :return: None
        """
        return self.verwijder_vplankoppelingen_by_uuid(asset_uuid=asset.uuid, vplankoppeling_uuids=vplankoppeling_uuids)

    def verwijder_alle_vplankoppelingen_by_uuid(self, asset_uuid: str) -> None:
        """
        Verwijder alle VPlan koppelingen van een asset.

        :param asset_uuid: Asset UUID
        :type asset_uuid: str
        :return: None
        """
        vplankoppelingen = self.get_vplankoppelingen_by_uuid(asset_uuid=asset_uuid)
        if not vplankoppelingen:
            logging.info(f"No VPlan koppelingen to remove for asset {asset_uuid}")
            return
        vplankoppeling_uuids = [koppeling['uuid'] for koppeling in vplankoppelingen]
        self.verwijder_vplankoppelingen_by_uuid(asset_uuid=asset_uuid, vplankoppeling_uuids=vplankoppeling_uuids)

    def verwijder_alle_vplankoppelingen(self, asset) -> None:
        """
        Verwijder alle VPlan koppelingen van een asset.

        :param asset: Asset
        :type asset: AssetDTO
        :return: None
        """
        return self.verwijder_alle_vplankoppelingen_by_uuid(asset_uuid=asset.uuid)
