from pathlib import Path

from openpyxl import load_workbook

from API.Enums import AuthType, Environment
from API.eminfra.EMInfraClient import EMInfraClient

ASSET_PREFIX = 'https://apps.mow.vlaanderen.be/eminfra/core/api/otl/assets/'
UUID_LENGTH = 36
LAAGSPANNINGSBORD_TYPE_URI = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Laagspanningsbord'
RESULT_COLUMN_TITLE = 'c.uuid'


def extract_asset_uuid_from_url(value: str | None) -> str | None:
    if not value:
        return None

    url = str(value).strip()
    if not url.startswith(ASSET_PREFIX):
        return None

    return url[len(ASSET_PREFIX): len(ASSET_PREFIX) + UUID_LENGTH]


def get_result_column_index(worksheet) -> int:
    for cell in worksheet[1]:
        if cell.value == RESULT_COLUMN_TITLE:
            return cell.column

    result_column = worksheet.max_column + 1
    worksheet.cell(row=1, column=result_column, value=RESULT_COLUMN_TITLE)
    return result_column


if __name__ == '__main__':

    settings_path = Path('/home/davidlinux/Documenten/AWV/resources/settings_SyncOTLDataToLegacy.json')
    eminfra_client = EMInfraClient(env=Environment.PRD, auth_type=AuthType.JWT, settings_path=settings_path)

    excel_path = Path(__file__).with_name('Keuringsrapporten info.xlsx')
    values_workbook = load_workbook(excel_path, data_only=True, read_only=True)
    values_worksheet = values_workbook.active
    worksheet = load_workbook(excel_path, data_only=False, read_only=False).active
    result_column = get_result_column_index(worksheet)

    for row_index, (value,) in enumerate(values_worksheet.iter_rows(min_row=2, min_col=3, max_col=3, values_only=True), start=2):
        uuid = extract_asset_uuid_from_url(value)
        c_uuids = []

        if uuid:
            for d in eminfra_client.document_service.get_documents_by_uuid_generator(asset_uuid=uuid, size=100):
                eminfra_client.document_service.download_document(document=d, directory=Path(__file__).parent)
    #         children = eminfra_client.asset_service.search_child_assets_by_uuid_generator(uuid, recursive=True)
    #         for c in children:
    #             if c.type.uri == LAAGSPANNINGSBORD_TYPE_URI:
    #                 c_uuids.append(c.uuid)
    #
    #     worksheet.cell(row=row_index, column=result_column, value='; '.join(c_uuids))
    #
    # worksheet.parent.save(excel_path)
