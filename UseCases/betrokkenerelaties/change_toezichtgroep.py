import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment
from API.eminfra.EMInfraDomain import BestekKoppeling, AssetDTO
from UseCases.utils import build_query_search_betrokkenerelaties

if __name__ == '__main__':
    input = []
    # Some parameters to test the functions.
    environment = Environment.PRD

    settings_path = Path('/home/davidlinux/Documenten/AWV/resources/settings_SyncOTLDataToLegacy.json')
    eminfra_client = EMInfraClient(env=environment, auth_type=AuthType.JWT, settings_path=settings_path)

    agent_cache = {}

    for input_row in input:
        add_relation = False
        asset_uuid = input_row[0]
        agent_name = input_row[1]

        query = build_query_search_betrokkenerelaties(bron_asset=AssetDTO(uuid=asset_uuid, links=None, _type=None, createdOn=None, modifiedOn=None, actief=None), rol='toezichtsgroep')
        relaties = list(eminfra_client.agent_service.search_betrokkenerelaties(query))
        if len(relaties) > 1:
            print(f'Found {len(relaties)} relations for asset {asset_uuid} and agent {agent_name}. Aborting.')
            removed_TOV_relation = False
            for relation in relaties:
                if relation.doel['naam'] == 'Tunnel Organ. VL.':
                    print('Removing relation with Tunnel Organ. VL.')
                    eminfra_client.agent_service.remove_betrokkenerelatie(relation.uuid)
                    removed_TOV_relation = True
            if not removed_TOV_relation:
                raise RuntimeError
            else:
                relaties = list(eminfra_client.agent_service.search_betrokkenerelaties(query))
        if len(relaties) == 1:
            if relaties[0].doel['naam'] == agent_name:
                print(f'Correction relation already existed for {asset_uuid} and {agent_name}')
                continue
            else:
                print(f'Relation found, but not correct. Expected {agent_name}, found {relaties[0].doel["naam"]}. Removing it...')
                eminfra_client.agent_service.remove_betrokkenerelatie(relaties[0].uuid)
                add_relation = True
        if len(relaties) == 0:
            if agent_name == 'UNKNOWN':
                print(f'No relation found for {asset_uuid} and {agent_name}. Skipping')
                continue
            print(f'No relation found for {asset_uuid} and {agent_name}. Creating new relation.')
            add_relation = True
        if add_relation:
            print(f'Adding relation for {asset_uuid} and {agent_name}')
            if agent_name not in agent_cache:
                print(f'Agent {agent_name} not found, creating it')
                agent = next(eminfra_client.agent_service.search_agent(naam=agent_name))
                if agent is not None:
                    agent_cache[agent_name] = agent.uuid
            eminfra_client.agent_service.add_betrokkenerelatie(
                asset=AssetDTO(uuid=asset_uuid, links=None, _type='onderdeel', createdOn=None, modifiedOn=None, actief=None),
                agent_uuid=agent_cache[agent_name], rol='toezichtsgroep')



