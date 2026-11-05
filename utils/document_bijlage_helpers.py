from __future__ import annotations

import logging
import re
from pathlib import Path

from API.clients.eminfra.EMInfraDomain import EigenschapValueDTO

KENMERK_UUID_BIJLAGE = "e67cd3d0-54b0-4db0-987d-9ef33e17d1ff"
_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def _parse_bijlage(eigenschapwaarde: EigenschapValueDTO) -> tuple[str, str | None]:
    value = eigenschapwaarde.typedValue.get("value") or {}
    bestandsnaam = str(value.get("bestandsnaam", "")).strip()
    uri = str(value.get("uri", ""))
    match = _UUID_RE.search(uri)
    return bestandsnaam, (match.group(0) if match else None)


def download_bijlage(
    client: EMInfraClient,
    output_folder: str | Path,
    asset_uuid: str,
    kenmerk_uuid: str = KENMERK_UUID_BIJLAGE,
    eigenschap_naam: str = "bijlage",
) -> Path | None:
    """Download the document referenced by eigenschap 'bijlage' for an asset.

    Returns the written Path, or None when no valid bijlage is available.
    """
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    eigenschapwaarden = client.eigenschap_service.get_eigenschapwaarden(
        asset_uuid=asset_uuid,
        kenmerk_uuid=kenmerk_uuid,
        eigenschap_naam=eigenschap_naam,
    )
    if len(eigenschapwaarden) != 1:
        logging.error(
            "Asset %s: expected 1 '%s' eigenschapwaarde, got %s",
            asset_uuid,
            eigenschap_naam,
            len(eigenschapwaarden),
        )
        return None

    bestandsnaam, document_uuid = _parse_bijlage(eigenschapwaarden[0])
    if not bestandsnaam or not document_uuid:
        logging.error("Asset %s: bijlage metadata incomplete (naam/uuid).", asset_uuid)
        return None

    # Sanitize filename (path traversal hardening).
    final_path = output_dir / Path(bestandsnaam).name
    response = client.requester.get(
        f"core/api/otl/assets/{asset_uuid}/documenten/{document_uuid}"
    )

    with open(final_path, "wb") as f:
        logging.info("Writing file %s to %s.", final_path.name, output_dir)
        f.write(response.content)
    return final_path