import json
import logging

from API.eminfra.EMInfraClient import EMInfraClient
from API.Enums import AuthType, Environment
from UseCases.utils import load_settings_path

DATA_FILE = '/home/davidlinux/PycharmProjects/VPlanMigration/output/bronassets_met_heeftvplan.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:\t%(asctime)s:\t%(message)s',
    filemode='w',
)


def main():
    settings_path = load_settings_path(user="David")
    eminfra_client = EMInfraClient(env=Environment.PRD, auth_type=AuthType.JWT, settings_path=settings_path)

    with open(DATA_FILE) as f:
        data = json.load(f)

    assets = data['assets']
    total = len(assets)
    logging.info(f'Starten met wissen van VPlan koppelingen voor {total} assets')

    success = 0
    skipped = 0
    errors = 0

    for i, asset_entry in enumerate(assets, 1):
        bron_asset_id = asset_entry['bronAssetId']
        asset_uuid = bron_asset_id[:36]

        if i % 100 == 0:
            logging.info(f'Vervolgen: {i}/{total} assets verwerkt')

        try:
            eminfra_client.vplan_service.verwijder_alle_vplankoppelingen_by_uuid(asset_uuid=asset_uuid)
            success += 1
        except Exception as e:
            logging.error(f'Fout bij asset {asset_uuid}: {e}')
            errors += 1
            skipped += 1

    logging.info(f'Klaar: {success} geslaagd, {skipped} overgeslagen, {errors} fouten')


if __name__ == '__main__':
    main()