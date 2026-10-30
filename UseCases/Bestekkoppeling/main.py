import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment
from API.eminfra.EMInfraDomain import BestekKoppeling, AssetDTO
from UseCases.utils import load_settings_path

if __name__ == '__main__':
    # Some parameters to test the functions.
    asset_uuid = '02e627c0-f8e9-4d33-9f06-57a100671d2f'
    environment = Environment.PRD


    settings_path = Path('/home/davidlinux/Documenten/AWV/resources/settings_SyncOTLDataToLegacy.json')
    eminfra_client = EMInfraClient(env=environment, auth_type=AuthType.JWT, settings_path=settings_path)

    vorig_dossiernummer = 'WA/OND/D100/2022/2_P1'
    vorig_bestek = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=vorig_dossiernummer)
    print(vorig_bestek)

    nieuw_besteknummer = 'WA/OND/D100/2026/3_P1'
    nieuw_bestek = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=nieuw_besteknummer)
    print(nieuw_bestek)
