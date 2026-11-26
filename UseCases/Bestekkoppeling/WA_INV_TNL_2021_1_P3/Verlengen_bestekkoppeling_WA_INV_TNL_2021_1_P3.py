import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from API.clients.eminfra.EMInfraClient import EMInfraClient
from API.clients.eminfra.EMInfraDomain import BestekCategorieEnum, BestekRef, BestekKoppeling, BestekKoppelingStatusEnum
from API.auth.enums import AuthType, Environment
from utils.date_helpers import format_datetime

EINDDATUM_BESTAAND = datetime(year=2026, month=12, day=1)
EINDDATUM_NIEUW = datetime(year=2027, month=8, day=31, hour=0, minute=0)
OUTPUT_EXCEL_PATH = Path('Verlengen_bestekkoppeling_WA_INV_TNL_2021_1_P3.xlsx')
EDELTA_DOSSIERNUMMER = 'WA/INV/TNL/2021/1_P3'


def verleng_bestekkoppelingen(client: EMInfraClient,
                              df: pd.DataFrame,
                              bestekref: BestekRef,
                              einddatum: datetime = EINDDATUM_NIEUW,
                              output_excel_path: Path = OUTPUT_EXCEL_PATH) -> Path:
    """
    Verleng de einddatum van bestekkoppelingen voor een lijst van uuid's (assets) in een Dataframe

    :param client:
    :type client:
    :param df: Dataframe met kolom uuid
    :type df: pd.Dataframe
    :param bestekref: Bestek referentie
    :type bestekref: BestekRef
    :param einddatum: einddatum waarnaar de bestekkoppeling wordt verlengd.
    :type einddatum: datetime
    :param output_excel_path: output Excel path
    :type output_excel_path: Path
    :return output file path
    """
    assets_updated = []
    for counter, df_row in df.iterrows():
        asset = client.asset_service.get_asset_by_uuid(asset_uuid=df_row["uuid"])
        logging.debug(f'Processing ({counter}) asset: {asset.uuid}; naam: {asset.naam}; assettype: {asset.type.uri}')

        bestekkoppelingen: list[BestekKoppeling] = client.bestek_service.get_bestekkoppeling(asset=asset)

        index, matching_bestekkoppeling = next(((i, x) for i, x in enumerate(bestekkoppelingen)
                                                if
                                                x.bestekRef.uuid == bestekref.uuid and
                                                x.categorie == BestekCategorieEnum.WERKBESTEK and
                                                datetime.fromisoformat(x.eindDatum).date() == EINDDATUM_BESTAAND.date() and
                                                x.status == BestekKoppelingStatusEnum.ACTIEF)
                                               , (None, None))

        if matching_bestekkoppeling:
            logging.debug(f'Verleng bestekkoppeling {matching_bestekkoppeling.bestekRef.eDeltaBesteknummer}')
            bestekkoppelingen[index].eindDatum = format_datetime(einddatum)
            # Update all the bestekkoppelingen for this asset
            assets_updated.append({
                "uuid": asset.uuid, "naam": asset.naam, "besteknummer": bestekref.eDeltaBesteknummer,
                "Start koppeling": matching_bestekkoppeling.startDatum,
                "Einde koppeling": matching_bestekkoppeling.eindDatum,
                "eminfra_link": f'https://apps.mow.vlaanderen.be/eminfra/assets/{asset.uuid}'
            })
            client.bestek_service.change_bestekkoppelingen(asset=asset, bestekkoppelingen=bestekkoppelingen)
        else:
            logging.debug('geen overeenkomstige bestekkoppeling gevonden, ga verder met de volgende asset.')
            continue

    df = pd.DataFrame(assets_updated)
    mode: str = 'a' if Path(output_excel_path).exists() else 'w'
    if mode == 'a':
        with pd.ExcelWriter(output_excel_path, mode=mode, engine='openpyxl', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name='overzicht', index=False, freeze_panes=(1, 1))
    elif mode == 'w':
        with pd.ExcelWriter(output_excel_path, mode='w', engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='overzicht', index=False, freeze_panes=(1, 1))
    return output_excel_path


if __name__ == '__main__':
    config_path = Path(__file__).parent.parent / "config" / "settings_AWV_applications.json.json"
    logging.info(
        f'Verlengen van bestekkoppeling "{EDELTA_DOSSIERNUMMER}" naar {format_datetime(EINDDATUM_NIEUW)}.'
    )
    eminfra_client = EMInfraClient(env=Environment.PRD, auth_type=AuthType.JWT, settings_path=config_path)

    logging.info("Query assets...")
    input_filepath = Path.home() / 'Downloads' / '[RSA] Bestekkoppelingen die bijna vervallen (komende 30 dagen).xlsx'
    df_assets = pd.read_excel(input_filepath, sheet_name='Resultaat', header=2, usecols=["uuid", "naampad"])
    bestekref = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=EDELTA_DOSSIERNUMMER)
    verleng_bestekkoppelingen(client=eminfra_client, df=df_assets, bestekref=bestekref)
