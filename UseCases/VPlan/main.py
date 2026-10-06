import json

from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment
from UseCases.utils import load_settings_path

if __name__ == '__main__':
    asset_uuid = '0051a91f-d599-45cd-adc8-aba275371e5d'
    environment = Environment.PRD

    settings_path = load_settings_path(user="David")
    eminfra_client = EMInfraClient(env=environment, auth_type=AuthType.JWT, settings_path=settings_path)

    asset = eminfra_client.asset_service.get_asset_by_uuid(asset_uuid=asset_uuid)
    print(f'Asset: {asset.naam} ({asset.uuid})')


    eminfra_client.vplan_service.verwijder_alle_vplankoppelingen(asset=asset)


    vplankoppelingen = eminfra_client.vplan_service.get_vplankoppelingen(asset=asset)

    print(f'Aantal vplankoppelingen: {len(vplankoppelingen)}')
    for i, koppeling in enumerate(vplankoppelingen, 1):
        print(f'\nKoppeling {i}:')
        print(json.dumps(koppeling, indent=2, ensure_ascii=False))