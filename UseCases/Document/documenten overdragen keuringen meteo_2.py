from datetime import datetime, date
from pathlib import Path

from openpyxl import load_workbook
from otlmow_converter.OtlmowConverter import OtlmowConverter
from otlmow_model.OtlmowModel.Classes.Installatie.Meteostation import Meteostation
from otlmow_model.OtlmowModel.Classes.Onderdeel.ElektrischeKeuring import ElektrischeKeuring
from otlmow_model.OtlmowModel.Classes.Onderdeel.HeeftKeuring import HeeftKeuring
from otlmow_model.OtlmowModel.Datatypes import DtcDocument
from otlmow_model.OtlmowModel.Datatypes.DtcDocument import DtcDocumentWaarden
from otlmow_model.OtlmowModel.Helpers.RelationCreator import create_relation

from API.Enums import AuthType, Environment
from API.eminfra.EMInfraClient import EMInfraClient
from otlmow_model.OtlmowModel.Classes.Onderdeel.Laagspanningsbord import Laagspanningsbord

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

    assets_to_create = []
    assets_to_create_2 = []

    for row_index, row_values in enumerate(values_worksheet.iter_rows(min_row=2, min_col=1, values_only=True), start=2):
        value = row_values[2]
        uuid = extract_asset_uuid_from_url(value)

        bestandsnaam = row_values[0].split('.pdf')[0]

        m = Meteostation()
        m.assetId.identificator = f'{uuid}-aW5zdGFsbGF0aWUjTWV0ZW9zdGF0aW9u'
        assets_to_create_2.append(m)

        l = Laagspanningsbord()
        l.assetId.identificator = f'{row_values[5]}-b25kZXJkZWVsI0xhYWdzcGFubmluZ3Nib3Jk'

        keuring = ElektrischeKeuring()
        keuring.assetId.identificator = f'keuring_van_{row_values[5]}'
        keuring.toestand = 'in-gebruik'
        keuring.naam = bestandsnaam
        value = row_values[3]
        if isinstance(value, datetime):
            keuring.keuringsdatum = date(value.year, value.month, value.day)
        else:
            text = str(value).strip()
            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(text, fmt)
                    keuring.keuringsdatum = date(dt.year, dt.month, dt.day)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Onbekend datumnotatie: {text!r}")
        keuring.resultaat = 'conform'

        # de bestandsnaam is soms var bestandsnaam + .pdf, maar soms ook nog met iets extra ertussen
        # de juiste bestandsnaam moet worden opgehaald en ingevuld
        # de bestanden staan in Path(__file__) / 'keuringsrapporten'
        # als er geen match is, print een error
        bestandsnaam = row_values[0]

        bestandsnaam = Path(__file__).parent / 'keuringsrapporten' / Path(bestandsnaam).with_suffix('.pdf')

        if not bestandsnaam.exists():
            # geen match = zoeken op eerste stuk van het bestand (alles voor "_")
            # als er dan wel een bestand gevonden wordt, gebruik dat
            keuringsrapporten_dir = Path(__file__).parent / 'keuringsrapporten'
            originele_bestandsnaam = Path(row_values[0])
            zoekterm = originele_bestandsnaam.stem.split('_')[0]  # Alles voor de eerste underscore
            
            gevonden_bestand = None
            for bestand in keuringsrapporten_dir.glob('*.pdf'):
                if bestand.stem.startswith(zoekterm):
                    gevonden_bestand = bestand
                    break
            
            if gevonden_bestand:
                bestandsnaam = gevonden_bestand
            else:
                print(f'Error: bestand {bestandsnaam} niet gevonden voor row {row_index}')
                continue
        dtc_doc = DtcDocumentWaarden()
        dtc_doc.bestandsnaam = bestandsnaam.name
        dtc_doc.mimeType = 'application/pdf'
        dtc_doc.opmaakdatum = keuring.keuringsdatum
        keuring.bijlage = dtc_doc


        assets_to_create.append(keuring)

        rel = create_relation(source=l, target=keuring, relation_type=HeeftKeuring)
        assets_to_create.append(rel)

        print(f'row {row_index}: bestand={row_values[0]} | asset_uuid={uuid or ""} | c.uuid={row_values[5]}')

    if assets_to_create:
        OtlmowConverter.to_file(subject=assets_to_create, file_path=Path(__file__).with_name('output.json'))

    if assets_to_create_2:
        OtlmowConverter.to_file(subject=assets_to_create_2, file_path=Path(__file__).with_name('output_2.xlsx'))
