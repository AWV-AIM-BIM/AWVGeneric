import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

log_file = Path(__file__).with_suffix(".log").name
logging.basicConfig(filename=log_file,
                    level=logging.DEBUG,
                    format='%(levelname)s:\t%(asctime)s:\t%(message)s\t',
                    filemode="w"
                    )

from utils.date_helpers import format_datetime
from API.clients.eminfra.EMInfraClient import EMInfraClient
from API.auth.enums import AuthType, Environment

ENVIRONMENT = Environment.PRD
BESTANDSNAAM = 'export_20261117144401.xlsx'
BESTEKNUMMER_OLD = 'MDM/19A02'
BESTEKNUMMER_NEW = 'II/2024/1'
DATUM_TRANSITIE = datetime(year=2026, month=11, day=1)
DATUM_TRANSITIE_FORMATTED = format_datetime(DATUM_TRANSITIE)


def read_excel_as_df(filepath: Path, sheet_name: str, usecols: list = None) -> pd.DataFrame:
    if not filepath.exists():
        raise FileNotFoundError(f'Filepath "{filepath}" does not exist.')

    if not usecols:
        usecols = ['assetId.identificator', 'typeURI']

    df = pd.read_excel(filepath, sheet_name=sheet_name, header=0, usecols=usecols)
    df = df.rename(columns={'assetId.identificator': 'uuid', 'id': 'uuid'})
    df = df.dropna(subset=["uuid"])
    return df


if __name__ == '__main__':
    logging.info('Beëindig een bestaande bestekkoppeling.\nVoeg een nieuwe bestekkoppeling toe.')

    logging.info(f'Omgeving: {ENVIRONMENT.name}')
    config_path = Path(__file__).parent.parent / "config" / "settings_AWV_applications.json"
    client = EMInfraClient(auth_type=AuthType.JWT, env=ENVIRONMENT, settings_path=config_path)

    # Read Excel as pandas dataframe
    excel_file = Path(__file__).parent / BESTANDSNAAM
    df_assets = read_excel_as_df(filepath=excel_file, sheet_name="Sheet0", usecols=["id", "naampad", "type"])
    df_assets_length = len(df_assets)

    for idx, df_row in df_assets.iterrows():
        logging.debug(f'Processing asset ({int(idx) + 1}/{df_assets_length}):'
                      f'\n\tasset_uuid: {df_row["uuid"]}')
        asset = client.asset_service.get_asset_by_uuid(asset_uuid=df_row["uuid"])

        if not asset:
            log_message = 'Asset onbestaande. Maak eerst de asset aan.'
            logging.warning(log_message)
            raise ValueError(log_message)

        # ophalen van de huidige/bestaande/actuele bestekkoppeling
        bestekkoppelingen = client.bestek_service.get_bestekkoppeling_by_uuid(asset_uuid=asset.uuid)

        # Check if bestekkoppeling exists: Apply existing function replace_bestekkoppeling_by_uuid()
        if matching_koppeling := next(
                (k for k in bestekkoppelingen if k.bestekRef.eDeltaBesteknummer == BESTEKNUMMER_OLD), None, ):
            logging.debug(f'Bestekkoppeling "{BESTEKNUMMER_OLD}" bestaat reeds, '
                          f'einddatum wordt ingesteld '
                          f'en een nieuwe bestekkoppeling gaat in vanaf datum: {DATUM_TRANSITIE}.')
            result_dict = client.bestek_service.replace_bestekkoppeling_by_uuid(
                asset_uuid=asset.uuid,
                eDelta_besteknummer_old=BESTEKNUMMER_OLD,
                eDelta_besteknummer_new=BESTEKNUMMER_NEW,
                start_datetime=DATUM_TRANSITIE
            )
        else:
            logging.critical(f'Bestekkoppeling "{BESTEKNUMMER_OLD}" bestaat niet.'
                          f'Inspecteer deze asset.')