from datetime import datetime
import logging
from pathlib import Path
import pandas as pd

from API.eminfra.EMInfraDomain import BestekCategorieEnum, BestekKoppelingStatusEnum, BestekKoppeling
from UseCases.utils import load_settings_path
from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment
from utils.date_helpers import format_datetime

ENVIRONMENT = Environment.PRD
BESTANDSNAAM = 'assets_bestekRefs.xlsx'
EDELTA_DOSSIERNUMMER = 'INTERN-429'
STARTDATUM = datetime(year=2026, month=6, day=1)
STARTDATUM_FORMATTED = format_datetime(STARTDATUM)
EINDDDATUM = None

def read_excel_as_df(filepath: Path, usecols: list = None) -> pd.DataFrame:
    if not filepath.exists():
        raise FileNotFoundError(f'Filepath "{filepath}" does not exist.')

    if not usecols:
        usecols = ['assetId.identificator', 'typeURI', 'bs.AwvId.identificator', 'bs.bestekRefId.identificator',
                   'bs.besteknummer']

    df = pd.read_excel(filepath, sheet_name='assets_zonder_bestek', header=0, usecols=usecols)
    df = df.rename(columns={
        'assetId.identificator': 'uuid',
        'bs.AwvId.identificator': 'bestekRefAwv_uuid',
        'bs.bestekRefId.identificator': 'bestekRef_uuid',
        'bs.besteknummer': 'bestekNummer'
    })
    df = df.dropna(subset=["uuid"])
    return df


if __name__ == '__main__':
    logging.basicConfig(filename="logs.log", level=logging.DEBUG, format='%(levelname)s:\t%(asctime)s:\t%(message)s\t',
                        filemode="w")
    logging.info('Voeg een tweede actieve bestekkoppeling toe: INTERN-429.')

    logging.info(f'Omgeving: {ENVIRONMENT.name}')
    eminfra_client = EMInfraClient(auth_type=AuthType.JWT, env=ENVIRONMENT, settings_path=load_settings_path())

    # Read Excel as pandas dataframe
    excel_file = (Path.home() / 'OneDrive - Nordend' / 'projects' / 'AWV' / '0_projecten_awv' / 'Bestekken' /
                  'intern-bestek 429' / BESTANDSNAAM)

    df_assets = read_excel_as_df(filepath=excel_file)
    df_assets_length = len(df_assets)

    # nieuwe bestekkoppeling
    bestekRef_new = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=EDELTA_DOSSIERNUMMER)

    for idx, df_row in df_assets.iterrows():
        logging.debug(f'Processing asset ({int(idx) + 1}/{df_assets_length}):'
                      f'\n\tasset_uuid: {df_row["uuid"]}')
        asset = eminfra_client.asset_service.get_asset_by_uuid(asset_uuid=df_row["uuid"][:36])

        if not asset:
            log_message = 'Asset onbestaande. Maak eerst de asset aan.'
            logging.warning(log_message)
            raise ValueError(log_message)

        bestekRef_uuid = df_row["bestekRef_uuid"]
        bestekNummer = df_row['bestekNummer']

        # ophalen van de huidige/bestaande/actuele bestekkoppeling
        bestekkoppelingen = eminfra_client.bestek_service.get_bestekkoppeling_by_uuid(asset_uuid=asset.uuid)

        # Check if bestekkoppeling exists: Apply existing function replace_bestekkoppeling_by_uuid()
        bestekkoppeling_new = None
        idx_matching_bestek = None
        for i, koppeling in enumerate(bestekkoppelingen):
            if koppeling.bestekRef.uuid == bestekRef_uuid:
                logging.debug(f'Bestek "{bestekNummer}" bestaat op index positie: {i}.')

                bestekkoppeling_new = BestekKoppeling(
                    bestekRef=bestekRef_new,
                    status=BestekKoppelingStatusEnum.ACTIEF,
                    startDatum=STARTDATUM_FORMATTED,
                    eindDatum=EINDDDATUM,
                    categorie=BestekCategorieEnum.WERKBESTEK
                )
                idx_matching_bestek=  i

            else:
                logging.info(f'Ander bestek, geen actie.')

        # Insert the new bestekkoppeling at index position i+1 (not append())
        # Insertion outside the loop
        if bestekkoppeling_new:
            bestekkoppelingen.insert(idx_matching_bestek + 1, bestekkoppeling_new)

        eminfra_client.bestek_service.change_bestekkoppelingen_by_uuid(asset_uuid=asset.uuid, bestekkoppelingen=bestekkoppelingen)