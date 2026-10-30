import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from API import AWVAppAuthenticator
from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment
from API.eminfra.EMInfraDomain import BestekKoppeling, BestekKoppelingStatusEnum, BestekCategorieEnum, QueryDTO, \
    PagingModeEnum, SelectionDTO, ExpressionDTO, TermDTO, OperatorEnum
from UseCases.utils import load_settings_path
from utils.date_helpers import format_datetime


if __name__ == '__main__':
    # Some parameters to test the functions.
    environment = Environment.PRD

    auth = AWVAppAuthenticator(env=environment, auth_type=AuthType.JWT)
    eminfra_client = auth.eminfra()  # or pass authenticator to EMInfraClient

    vorig_dossiernummer = 'WA/OND/D100/2022/2_P1'
    vorig_bestek = eminfra_client.bestek_service.get_bestekref(eDelta_dossiernummer=vorig_dossiernummer)
    print(vorig_bestek)

