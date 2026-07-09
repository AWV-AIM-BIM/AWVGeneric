import logging

import pandas as pd

from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment

from UseCases.utils import load_settings_path, configure_logger, build_query_search_betrokkenerelaties, update_agent

EXCEL_FILEPATH = 'keuringsinfo_20260611_114736_met_inbreuken.xlsx'
SHEETNAME = 'verzameling_assets'
ENVIRONMENT = Environment.PRD
HYPERLINK_FIRST_PART = 'https://apps.mow.vlaanderen.be/eminfra/assets/'


if __name__ == '__main__':
    configure_logger()
    logging.info('Update betrokkenerelaties van agents die zijn gekoppeld aan Laagspanningsborden\t '
                 'Update om een correcte AREI rapportage te verkrijgen, waarbij de assets v.h. type Laagspanningsbord'
                 'de correcte toezichter/toezichtsgroep/schadebeheerder is toegewezen.')
    eminfra_client = EMInfraClient(env=ENVIRONMENT, auth_type=AuthType.JWT, settings_path=load_settings_path())

    logging.info('Inlezen Excel bestand.')
    df_assets = pd.read_excel(EXCEL_FILEPATH, sheet_name=SHEETNAME, header=0,
                              usecols=["uuid", "toezichtgroep", "toezichter", "schadebeheerder"])

    logging.info('Loop over dataframe and check if asset exists.')
    df_length = len(df_assets)
    rows = []
    for idx, df_row in df_assets.iterrows():
        logging.info(f'Ophalen asset ({int(idx)+1}/{df_length}): {df_row["uuid"]}')
        asset = eminfra_client.asset_service.get_asset_by_uuid(asset_uuid=df_row["uuid"])

        logging.info(f'Ophalen van de betrokkenerelatie(s) voor asset ({asset.uuid}) en rollen '
                     f'("toezichter", toezichtgroep", "schadebeheerder").')
        toezichter, toezichtgroep, schadebeheerder = (
            df_row["toezichter"], df_row["toezichtgroep"], df_row["schadebeheerder"])

        if not pd.isna(toezichter):
            update_agent(eminfra_client=eminfra_client, asset=asset, agent_naam=toezichter, agent_rol='toezichter')
        if not pd.isna(toezichtgroep):
            update_agent(eminfra_client=eminfra_client, asset=asset, agent_naam=toezichtgroep, agent_rol='toezichtsgroep')
        if not pd.isna(schadebeheerder):
            update_agent(eminfra_client=eminfra_client, asset=asset, agent_naam=schadebeheerder, agent_rol='schadebeheerder')

        row = {
            "uuid": asset.uuid,
            "uuid.hyperlink": f'{HYPERLINK_FIRST_PART}{asset.uuid}',
            "toezichter": toezichter,
            "toezichtsgroep": toezichtgroep,
            "schadebeheerder": schadebeheerder
        }
        rows.append(row)

    output_excel_path = f'output_update_Agents_LSBord.xlsx'

    # Write to a new file (! overwrite each run)
    with pd.ExcelWriter(output_excel_path, mode='w', engine='openpyxl') as writer:
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='Sheet1', index=False, freeze_panes=(1, 2))