from API.Enums import Environment
from API.eminfra.EMInfraDomain import QueryDTO, PagingModeEnum, SelectionDTO, ExpressionDTO, OperatorEnum, TermDTO, \
    LogicalOpEnum

ENVIRONMENT = Environment.PRD

AGENT_UUID_TOV1 = '7aa92dda-9e03-4f10-a0b3-1c6748c332b9'
if ENVIRONMENT.name == 'TEI':
    AGENT_UUID_TOV2 = 'd6a702c1-d3b2-4162-9b99-f6499ad88a22'
    HYPERLINK_FIRST_PART = 'https://apps-tei.mow.vlaanderen.be/eminfra/assets/'
else:
    AGENT_UUID_TOV2 = '2a484172-54d9-45bf-97c5-96019c5ec803'
    HYPERLINK_FIRST_PART = 'https://apps.mow.vlaanderen.be/eminfra/assets/'

# df_assets = read_rsa_report()
query_dto_assets_TOV1 = QueryDTO(
    size=100, from_=0, pagingMode=PagingModeEnum.OFFSET,
    selection=SelectionDTO(
        expressions=[
            ExpressionDTO(
                terms=[TermDTO(
                    property='agent',
                    operator=OperatorEnum.EQ,
                    value=AGENT_UUID_TOV1),
                TermDTO(property='actief',
                        operator=OperatorEnum.EQ,
                        value=True,
                        logicalOp=LogicalOpEnum.AND)]
            )
        ]))