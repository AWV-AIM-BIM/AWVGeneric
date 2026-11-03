import logging
from datetime import datetime

from API.eminfra.EMInfraClient import EMInfraClient
from API.eminfra.EMInfraDomain import (
    QueryDTO, PagingModeEnum, SelectionDTO, ExpressionDTO, TermDTO,
    OperatorEnum, LogicalOpEnum, ExpansionsDTO, construct_naampad,
)
from API.Enums import AuthType, Environment
from UseCases.utils import load_settings_path

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    environment = Environment.PRD
    settings_path = load_settings_path()
    eminfra_client = EMInfraClient(env=environment, auth_type=AuthType.JWT, settings_path=settings_path)

    # Query all active assets; parent expansion needed to build naampad.
    query_dto = QueryDTO(
        size=100, from_=0, pagingMode=PagingModeEnum.OFFSET,
        expansions=ExpansionsDTO(fields=['parent']),
        selection=SelectionDTO(expressions=[
            ExpressionDTO(terms=[TermDTO(property='actief', operator=OperatorEnum.EQ, value=True)]),
            ExpressionDTO(terms=[TermDTO(property='naamPad', operator=OperatorEnum.STARTS_WITH, value='MET')], logicalOp=LogicalOpEnum.AND),
            # ExpressionDTO(terms=[TermDTO(property='beheerobject', operator=OperatorEnum.EQ, value=None)], logicalOp=LogicalOpEnum.AND),
        ]),
    )

    erroneous_end_date = datetime(2027, 10, 30)
    new_end_date = datetime(2026, 12, 31)

    assets = eminfra_client.asset_service.search_assets_generator(query_dto=query_dto)

    for asset in assets:
        naampad = construct_naampad(asset)
        if not naampad.startswith('MET'):
            continue

        logging.info(f"Asset {asset.uuid} - {naampad}")

        # Retrieve its postits and update each one's end date.
        postits = eminfra_client.postit_service.search_postits_generator(asset_uuid=asset.uuid)
        for postit in postits:
            # check actual post-it enddate
            postit_einddatum = datetime.fromisoformat(postit.eindDatum)
            if postit_einddatum.date() != erroneous_end_date.date():
                logging.info(f"  postit {postit.uuid}: {postit.commentaar} met einddatum: {postit_einddatum}")
                continue

            logging.info(f"  postit {postit.uuid}: {postit.commentaar} met einddatum: {postit_einddatum}")

            # apply edit_postit() to update enddate
            eminfra_client.postit_service.edit_postit(
                asset_uuid=asset.uuid,
                postit_uuid=postit.uuid,
                eind_datum=new_end_date,
            )
            logging.info(f"  updated enddate to {new_end_date}")