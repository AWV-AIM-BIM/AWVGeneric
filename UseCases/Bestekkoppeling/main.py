import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment
from API.eminfra.EMInfraDomain import BestekKoppeling, BestekKoppelingStatusEnum, BestekCategorieEnum, QueryDTO, \
    PagingModeEnum, SelectionDTO, ExpressionDTO, TermDTO, OperatorEnum
from UseCases.utils import load_settings_path
from utils.date_helpers import format_datetime


if __name__ == '__main__':
    # Some parameters to test the functions.
    environment = Environment.PRD

    settings_path = Path('/home/davidlinux/Documenten/AWV/resources/settings_SyncOTLDataToLegacy.json')
    eminfra_client = EMInfraClient(env=environment, auth_type=AuthType.JWT, settings_path=settings_path)

    vorig_dossiernummer = 'WA/OND/D100/2022/2_P1'
    vorig_bestek = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=vorig_dossiernummer)
    print(vorig_bestek)

    nieuw_besteknummer = 'WA/OND/D100/2026/3_P1'
    nieuw_bestek = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=nieuw_besteknummer)
    print(nieuw_bestek)

    intern_besteknummers = ['INTERN-1992', 'INTERN-1993', 'INTERN-1994', 'INTERN-1995', 'INTERN-1996']
    intern_bestek_uuids = set()
    for nummer in intern_besteknummers:
        intern_bestek = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=nummer)
        intern_bestek_uuids.add(intern_bestek.uuid)

    vandaag = datetime.now()

    # Zoek alle assets die een actieve koppeling hebben met "vorig bestek"
    query_dto = QueryDTO(
        size=100,
        from_=0,
        pagingMode=PagingModeEnum.OFFSET,
        selection=SelectionDTO(
            expressions=[ExpressionDTO(
                terms=[
                    TermDTO(property='actiefBestek', operator=OperatorEnum.EQ, value=vorig_bestek.uuid)
                ])
            ])
    )

    assets = eminfra_client.asset_service.search_assets(query_dto=query_dto, actief=True)

    for asset in assets:
        bestekkoppelingen = eminfra_client.bestek_service.get_bestekkoppeling_by_uuid(asset_uuid=asset.uuid)

        # Zoek index van koppeling met "vorig bestek"
        index_vorig = next((i for i, item in enumerate(bestekkoppelingen) if item.bestekRef.uuid == vorig_bestek.uuid), None)

        if index_vorig is None:
            continue

        # Koppeling met "vorig bestek" krijgt einddatum vandaag
        koppeling_vorig = bestekkoppelingen[index_vorig]
        koppeling_vorig.eindDatum = format_datetime(vandaag)
        koppeling_vorig.status = BestekKoppelingStatusEnum.INACTIEF

        # Koppeling met nieuw bestek invoegen op die plaats (dus voor vorig bestek) met begindatum vandaag en geen einddatum
        if not any(k.bestekRef.uuid == nieuw_bestek.uuid for k in bestekkoppelingen):
            koppeling_nieuw = BestekKoppeling(
                bestekRef=nieuw_bestek,
                startDatum=format_datetime(vandaag),
                eindDatum=None,
                categorie=BestekCategorieEnum.WERKBESTEK
            )
            bestekkoppelingen.insert(index_vorig, koppeling_nieuw)
        else:
            continue

        # Controleren dat een van de interne bestekken nog steeds als eerste in de rij staat, anders in console printen
        if len(bestekkoppelingen) == 0 or bestekkoppelingen[0].bestekRef.uuid not in intern_bestek_uuids:
            print(f"intern_bestek staat niet als eerste voor asset {asset.uuid}")

        eminfra_client.bestek_service.change_bestekkoppelingen_by_uuid(asset_uuid=asset.uuid, bestekkoppelingen=bestekkoppelingen)
