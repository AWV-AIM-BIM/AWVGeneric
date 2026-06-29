import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

from UseCases.utils import load_settings_path
from utils.date_helpers import format_datetime
from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment

ENVIRONMENT = Environment.PRD
BESTANDSNAAM = f'export-selectielijst_20260526_clipped.xlsx'
BESTEKNUMMER_OLD = 'MDM/17K02'
BESTEKNUMMER_NEW = 'VWT/DVM/2023/3'
DATUM_TRANSITIE = datetime(year=2026, month=7, day=1)
DATUM_TRANSITIE_FORMATTED = format_datetime(datetime(year=2026, month=7, day=1))

def read_excel_as_df(filepath: Path, usecols: list = None) -> pd.DataFrame:
    if not filepath.exists():
        raise FileNotFoundError(f'Filepath "{filepath}" does not exist.')

    if not usecols:
        usecols = ['assetId.identificator', 'typeURI']

    df = pd.read_excel(filepath, sheet_name='Selectielijst_17K02', header=0, usecols=usecols)
    df = df.rename(columns={'assetId.identificator': 'uuid'})
    df = df.dropna(subset=["uuid"])
    return df


if __name__ == '__main__':
    logging.basicConfig(filename="logs.log", level=logging.DEBUG, format='%(levelname)s:\t%(asctime)s:\t%(message)s\t',
                        filemode="w")
    logging.info('Beëindig een bestaande bestekkoppeling.\nVoeg een nieuwe bestekkoppeling toe.')

    logging.info(f'Omgeving: {ENVIRONMENT.name}')
    eminfra_client = EMInfraClient(auth_type=AuthType.JWT, env=ENVIRONMENT, settings_path=load_settings_path())

    # overbodig, dit kan wss geschrapt worden
    bestekref_17K02 = eminfra_client.bestek_service.get_bestekref(eDelta_besteknummer=BESTEKNUMMER_OLD)

    # Read Excel as pandas dataframe
    excel_file = (Path.home() / 'OneDrive - Nordend' / 'projects' / 'AWV' / '0_projecten_awv' / 'BenCannaerts' /
                  'E40_LeuvenBrussel' / BESTANDSNAAM)

    df_assets = read_excel_as_df(filepath=excel_file)
    df_assets_length = len(df_assets)

    for idx, df_row in df_assets.iterrows():
        logging.debug(f'Processing asset ({int(idx) + 1}/{df_assets_length}):'
                      f'\n\tasset_uuid: {df_row["uuid"]}')
        asset = eminfra_client.asset_service.get_asset_by_uuid(asset_uuid=df_row["uuid"][:36])

        if not asset:
            log_message = 'Asset onbestaande. Maak eerst de asset aan.'
            logging.warning(log_message)
            raise ValueError(log_message)

        # ophalen van de huidige/bestaande/actuele bestekkoppeling
        bestekkoppelingen = eminfra_client.bestek_service.get_bestekkoppeling_by_uuid(asset_uuid=asset.uuid)

        # Check if bestekkoppeling exists: Apply existing function replace_bestekkoppeling_by_uuid()
        if matching_koppeling := next(
                (k for k in bestekkoppelingen if k.bestekRef.eDeltaBesteknummer == BESTEKNUMMER_OLD), None, ):
            logging.debug(f'Bestekkoppeling "{BESTEKNUMMER_OLD}" bestaat reeds, '
                          f'einddatum wordt ingesteld '
                          f'en een nieuwe bestekkoppeling gaat in vanaf datum: {DATUM_TRANSITIE}.')
            result_dict = eminfra_client.bestek_service.replace_bestekkoppeling_by_uuid(
                asset_uuid=asset.uuid,
                eDelta_besteknummer_old=BESTEKNUMMER_OLD,
                eDelta_besteknummer_new=BESTEKNUMMER_NEW,
                start_datetime=DATUM_TRANSITIE
            )
        else:
            logging.critical(f'Bestekkoppeling "{BESTEKNUMMER_OLD}" bestaat niet.'
                          f'Inspecteer deze asset.')