"""
Standalone script: download all documents associated with assets listed in
ElektrischeKeuring_rapport.xlsx (column: assetId.Identificator).

Reads the fixed column structure from the Excel file and uses the 'bijlage'
column to name the output file. Each asset gets its own subfolder.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from API import AWVAppAuthenticator
from API.auth.enums import AuthType, Environment
from API.clients.eminfra.EMInfraClient import EMInfraClient
from API.clients.eminfra.EMInfraDomain import EigenschapValueDTO

from utils.document_bijlage_helpers import KENMERK_UUID_BIJLAGE, download_bijlage

EXCEL_FILE_NAME = "ElektrischeKeuring_rapport.xlsx"
EXCEL_COLUMNS = [
    "assetId.identificator",
    "typeURI",
    "isActief",
    "naam",
    "toestand",
    "bijlage",
    "eig_resultaat",
    "eig_keuringsdatum",
]
OUTPUT_DIR = Path.home() / "Downloads" / "Documenten_Keuring"

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
KENMERK_UUID_BIJLAGE = 'e67cd3d0-54b0-4db0-987d-9ef33e17d1ff'


def extract_asset_uuid(value: str | None) -> str | None:
    """Return a UUID from an identificator (bare UUID or uuid-<suffix>)."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = UUID_RE.search(text)
    return match.group(0) if match else text


def read_keuringen(excel_path: Path) -> pd.DataFrame:
    """Read the Excel file into a DataFrame with the fixed column structure."""
    df = pd.read_excel(excel_path, sheet_name="assets", dtype=str)
    missing = [col for col in EXCEL_COLUMNS if col not in df.columns]
    if missing:
        raise KeyError(
            f"Missing columns {missing} in {excel_path.name}. "
            f"Available columns: {list(df.columns)}"
        )
    return df[EXCEL_COLUMNS]


def _parse_bijlage_from_eigenschapwaarde(eigenschapwaarde: EigenschapValueDTO) -> tuple[str, str, str|None]:
    """
    Returns bestandsnaam, uri and document_uuid from eigenschapwaarde
    """
    value = eigenschapwaarde.typedValue.get('value')
    bestandsnaam = str(value.get('bestandsnaam'))
    uri = str(value.get('uri'))
    match = UUID_RE.search(uri)
    document_uuid = match.group(0) if match else None
    return bestandsnaam, uri, document_uuid


def download_documents_for_assets(
    client: EMInfraClient, df: pd.DataFrame, output_dir: Path
) -> int:
    """Download every document of each asset. Returns total downloaded count."""
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for _, row in df.iterrows():
        asset_uuid = extract_asset_uuid(row["assetId.identificator"])
        if not asset_uuid:
            continue

        asset_dir = output_dir / asset_uuid
        try:
            path = download_bijlage(
                output_folder=asset_dir,
                asset_uuid=asset_uuid,
                client=client,
                kenmerk_uuid=KENMERK_UUID_BIJLAGE,
            )
            if path is not None:
                total += 1
        except Exception as exc:  # noqa: BLE001
            logging.error(
                "Kon document van asset %s niet downloaden: %s",
                asset_uuid,
                exc,
            )

    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # JWT-authenticatie:
    auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.JWT)
    client = EMInfraClient(authenticator=auth)

    excel_path = Path(__file__).with_name(EXCEL_FILE_NAME)
    df = read_keuringen(excel_path)
    print(f"{len(df)} rijen gelezen uit {excel_path.name}.")

    total = download_documents_for_assets(
        client=client, df=df, output_dir=OUTPUT_DIR
    )
    print(f"Klaar. {total} document(en) gedownload in: {OUTPUT_DIR}")