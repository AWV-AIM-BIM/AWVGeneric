import logging
from pathlib import Path
import pandas as pd

from UseCases.utils import load_settings_path
from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment

ENVIRONMENT = Environment.PRD
BESTANDSNAAM = 'assets_bestekRefs_tunnel.xlsx'

def read_excel_as_df(filepath: Path, usecols: list = None) -> pd.DataFrame:
    if not filepath.exists():
        raise FileNotFoundError(f'Filepath "{filepath}" does not exist.')

    if not usecols:
        usecols = ['assetId.identificator', 'typeURI', 'bs.AwvId.identificator', 'bs.besteknummer']

    df = pd.read_excel(filepath, sheet_name='Sheet1', header=0, usecols=usecols)
    df = df.rename(columns={
        'assetId.identificator': 'uuid',
        'bs.AwvId.identificator': 'bestekRef_uuid',
        'bs.besteknummer': 'bestekNummer'
    })
    df = df.dropna(subset=["uuid"])
    return df


if __name__ == '__main__':
    logging.basicConfig(filename="logs.log", level=logging.DEBUG, format='%(levelname)s:\t%(asctime)s:\t%(message)s\t',
                        filemode="w")
    logging.info('Voor de bestaande bestekkoppeling, wis de einddatum. Maak het een open einde zodat de bestekkoppeling niet vervalt op de huidige einddatum.')

    logging.info(f'Omgeving: {ENVIRONMENT.name}')
    eminfra_client = EMInfraClient(auth_type=AuthType.JWT, env=ENVIRONMENT, settings_path=load_settings_path())

    # Read Excel as pandas dataframe
    excel_file = (Path.home() / 'OneDrive - Nordend' / 'projects' / 'AWV' / '0_projecten_awv' / 'Patrick Van Ransbeek' /
                  '202607_bestekken verlengen' / BESTANDSNAAM)

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

        bestekRef_uuid = df_row["bestekRef_uuid"]
        bestekNummer = df_row['bestekNummer']

        # ophalen van de huidige/bestaande/actuele bestekkoppeling
        bestekkoppelingen = eminfra_client.bestek_service.get_bestekkoppeling_by_uuid(asset_uuid=asset.uuid)

        # Check if bestekkoppeling exists: Apply existing function replace_bestekkoppeling_by_uuid()
        if matching_koppeling := next(
                (k for k in bestekkoppelingen if k.bestekRef.eDeltaBesteknummer == bestekNummer), None, ):
            logging.debug(f'Bestek "{bestekNummer}" bestaat, '
                          f'einddatum wordt leeggemaakt.')
            start_datetime = matching_koppeling.startDatum
            eminfra_client.bestek_service.adjust_date_bestekkoppeling_by_uuid(
                asset_uuid=asset.uuid, bestek_ref_uuid=bestekRef_uuid, start_datetime=start_datetime, end_datetime=None)

        else:
            logging.critical(f'Ander bestek, geen actie.')