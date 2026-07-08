import logging

import pandas as pd
from agent_info import *

from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType

from UseCases.utils import load_settings_path, configure_logger, build_query_search_betrokkenerelaties

if __name__ == '__main__':
    configure_logger()
    logging.info('Update agent Tunnel Organisatie Vlaanderen:\t '
                 'Wijzig betrokkenerelatie die verwijst naar agent "Tunnel Organ. VL." door agent'
                 ' "Afdeling Tunnelorganisatie".')
    eminfra_client = EMInfraClient(env=ENVIRONMENT, auth_type=AuthType.JWT, settings_path=load_settings_path())

    assets_generator = eminfra_client.asset_service.search_assets_generator(query_dto=query_dto_assets_TOV1, actief=True)

    agent1 = next(eminfra_client.agent_service.search_agent(naam='Tunnel Organ. VL.'))
    agent2 = next(eminfra_client.agent_service.search_agent(naam='Afdeling Tunnelorganisatie'))

    asset_counter = 0
    rows = []
    for asset in assets_generator:
        asset_counter += 1
        logging.info(f"Processing asset ({asset_counter}):\tasset_uuid: {asset.uuid}")

        query_dto_betrokkenerelaties = build_query_search_betrokkenerelaties(bron_asset=asset, agent=agent1)
        betrokkenerelaties = eminfra_client.agent_service.search_betrokkenerelaties(
            query_dto=query_dto_betrokkenerelaties)

        for betrokkenerelatie in betrokkenerelaties:
            logging.info(f"Deactiveer betrokkenerelatie: {betrokkenerelatie.uuid}")
            eminfra_client.agent_service.remove_betrokkenerelatie(betrokkenerelatie_uuid=betrokkenerelatie.uuid)

            logging.info(f'Voeg nieuwe betrokkenerelatie toe, met dezelfde rol, maar naar een nieuwe agent.')
            betrokkenerelatie_new_dict = eminfra_client.agent_service.add_betrokkenerelatie(
                asset=asset, agent_uuid=AGENT_UUID_TOV2, rol=betrokkenerelatie.rol)

            row = {
                "uuid": asset.uuid,
                "uuid.hyperlink": f'{HYPERLINK_FIRST_PART}{asset.uuid}',
                "betrokkenerelatie_rol": betrokkenerelatie.rol,
                "betrokkenerelatie_uuid_old": betrokkenerelatie.uuid,
                "betrokkenerelatie_uuid_new": betrokkenerelatie_new_dict["uuid"]
            }
            rows.append(row)

    output_excel_path = f'test_output_{ENVIRONMENT.name}.xlsx'

    # Write to a new file (! overwrite each run)
    with pd.ExcelWriter(output_excel_path, mode='w', engine='openpyxl') as writer:
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='Sheet1', index=False, freeze_panes=(1, 2))