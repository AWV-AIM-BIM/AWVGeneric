#!/usr/bin/env python3
"""
UpdateBestekkoppeling_bestek.py

Production-ready script to migrate bestekkoppeling (contract links) for assets
from an old bestek number to a new one with a transition date.

This script reads asset UUIDs from an Excel file, retrieves each asset from EMInfra,
finds the existing bestekkoppeling matching the old bestek number, ends it on the
transition date, and creates a new bestekkoppeling with the new bestek number
starting from the transition date.

Usage:
    python UpdateBestekkoppeling_bestek.py 
        --excel export_20261117144401.xlsx 
        --old-bestek "MDM/19A02" 
        --new-bestek "II/2024/1" 
        --transition-date 2026-11-01 
        --env PRD 
        --config-path ../config/settings_AWV_applications.json

Author: AWV Development Team
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from utils.date_helpers import format_datetime
from API.clients.eminfra.EMInfraClient import EMInfraClient
from API.auth.enums import AuthType, Environment


# Custom Exceptions
class BestekkoppelingError(Exception):
    """Base exception for bestekkoppeling migration errors."""
    pass


class AssetNotFoundError(BestekkoppelingError):
    """Raised when an asset does not exist in EMInfra."""
    pass


class BestekkoppelingNotFoundError(BestekkoppelingError):
    """Raised when the expected bestekkoppeling is not found on an asset."""
    pass


class InvalidUUIDError(BestekkoppelingError):
    """Raised when a UUID string is malformed."""
    pass


class ConfigurationError(BestekkoppelingError):
    """Raised when configuration is invalid or missing."""
    pass


# Constants & Configuration
EXCEL_COLUMN_MAP = {
    "assetId.identificator": "uuid",
    "id": "uuid",
    "naampad": "naampad",
    "type": "type",
}

REQUIRED_COLUMNS = ["uuid"]

DEFAULT_SHEET_NAME = "Sheet0"
DEFAULT_LOG_FORMAT = "%(levelname)s:\t%(asctime)s:\t%(message)s\t"
MAX_RETRIES = 3
RETRY_MIN_WAIT = 2
RETRY_MAX_WAIT = 10


def validate_uuid(uuid_str: str) -> str:
    """Validate and normalize a UUID string."""
    try:
        parsed = uuid_lib.UUID(uuid_str)
        return str(parsed)
    except (ValueError, AttributeError) as exc:
        raise InvalidUUIDError(f"Invalid UUID format: '{uuid_str}'") from exc


def setup_logging(log_file: Path, level: int = logging.DEBUG) -> None:
    """Configure logging to both file and console."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate bestekkoppeling for assets from old to new bestek number.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--excel", type=Path, required=True, help="Path to Excel file containing asset UUIDs.")
    parser.add_argument("--old-bestek", required=True, help="Old bestek number to replace (e.g., 'MDM/19A02').")
    parser.add_argument("--new-bestek", required=True, help="New bestek number to assign (e.g., 'II/2024/1').")
    parser.add_argument("--transition-date", required=True, help="Transition date in ISO format (YYYY-MM-DD).")
    parser.add_argument("--env", choices=[e.name for e in Environment], default="PRD", help="Target environment.")
    parser.add_argument("--config-path", type=Path, default=Path(__file__).parent.parent / "config" / "settings_AWV_applications.json", help="Path to EMInfra settings JSON file.")
    parser.add_argument("--sheet-name", default=DEFAULT_SHEET_NAME, help="Excel sheet name to read.")
    parser.add_argument("--log-dir", type=Path, default=Path(__file__).parent, help="Directory for log file.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without making changes.")
    parser.add_argument("--resume-from", type=int, default=0, help="Resume from asset index (0-based).")

    return parser.parse_args()


def load_excel_assets(filepath: Path, sheet_name: str = DEFAULT_SHEET_NAME) -> pd.DataFrame:
    """Load and validate asset data from Excel file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Excel file not found: {filepath}")

    usecols = list(EXCEL_COLUMN_MAP.keys())
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=0, usecols=usecols)
    df = df.rename(columns=EXCEL_COLUMN_MAP)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ConfigurationError(f"Missing required columns in Excel: {missing}. Available: {list(df.columns)}")

    initial_count = len(df)
    df = df.dropna(subset=["uuid"])
    dropped = initial_count - len(df)
    if dropped:
        logging.warning(f"Dropped {dropped} rows with missing UUID.")

    def validate_row_uuid(uuid_val: str) -> str:
        return validate_uuid(str(uuid_val).strip())

    df["uuid"] = df["uuid"].apply(validate_row_uuid)

    logging.info(f"Loaded {len(df)} valid assets from {filepath} (sheet: {sheet_name})")
    return df


class EMInfraService:
    """Wrapper around EMInfraClient with retry logic and error handling."""

    def __init__(self, client: EMInfraClient) -> None:
        self._client = client

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT), retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)), reraise=True)
    def get_asset(self, asset_uuid: str) -> Optional[object]:
        asset = self._client.asset_service.get_asset_by_uuid(asset_uuid=asset_uuid)
        if asset is None:
            raise AssetNotFoundError(f"Asset not found: {asset_uuid}")
        return asset

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT), retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)), reraise=True)
    def get_bestekkoppelingen(self, asset_uuid: str) -> list:
        return self._client.bestek_service.get_bestekkoppeling_by_uuid(asset_uuid=asset_uuid)

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT), retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)), reraise=True)
    def replace_bestekkoppeling(self, asset_uuid: str, old_bestek: str, new_bestek: str, start_datetime: datetime) -> dict:
        return self._client.bestek_service.replace_bestekkoppeling_by_uuid(asset_uuid=asset_uuid, eDelta_besteknummer_old=old_bestek, eDelta_besteknummer_new=new_bestek, start_datetime=start_datetime)

    def find_matching_bestekkoppeling(self, bestekkoppelingen: list, bestek_nummer: str) -> Optional[object]:
        return next((k for k in bestekkoppelingen if getattr(k.bestekRef, "eDeltaBesteknummer", None) == bestek_nummer), None)


def process_asset(service: EMInfraService, asset_uuid: str, old_bestek: str, new_bestek: str, transition_dt: datetime, dry_run: bool = False) -> tuple[bool, str]:
    """Process a single asset: find old bestekkoppeling, end it, create new one."""
    try:
        asset = service.get_asset(asset_uuid)
        bestekkoppelingen = service.get_bestekkoppelingen(asset_uuid=asset.uuid)
        matching = service.find_matching_bestekkoppeling(bestekkoppelingen, old_bestek)

        if matching is None:
            msg = f'Bestekkoppeling "{old_bestek}" does not exist on asset {asset_uuid}.'
            logging.critical(msg)
            return False, msg

        logging.debug(f'Found bestekkoppeling "{old_bestek}" on asset {asset_uuid}. Will end it and start "{new_bestek}" from {transition_dt}.')

        if dry_run:
            msg = f"[DRY RUN] Would replace bestekkoppeling {old_bestek} -> {new_bestek} on asset {asset_uuid} at {transition_dt}"
            logging.info(msg)
            return True, msg

        result = service.replace_bestekkoppeling(asset_uuid=asset.uuid, old_bestek=old_bestek, new_bestek=new_bestek, start_datetime=transition_dt)
        msg = f"Successfully migrated asset {asset_uuid}: {result}"
        logging.info(msg)
        return True, msg

    except AssetNotFoundError as exc:
        msg = f"Asset not found: {exc}"
        logging.warning(msg)
        return False, msg

    except BestekkoppelingNotFoundError as exc:
        msg = f"Bestekkoppeling not found: {exc}"
        logging.critical(msg)
        return False, msg

    except Exception as exc:
        msg = f"Unexpected error processing asset {asset_uuid}: {exc}"
        logging.exception(msg)
        return False, msg


def run_migration(df_assets: pd.DataFrame, service: EMInfraService, old_bestek: str, new_bestek: str, transition_dt: datetime, dry_run: bool = False, resume_from: int = 0) -> dict:
    """Run migration for all assets in the DataFrame."""
    total = len(df_assets)
    stats = {"total": total, "processed": 0, "success": 0, "failed": 0, "skipped": 0, "errors": []}

    logging.info(f"Starting migration for {total} assets (resume from index {resume_from})")

    for idx, row in df_assets.iterrows():
        if idx < resume_from:
            stats["skipped"] += 1
            continue

        asset_uuid = row["uuid"]
        stats["processed"] += 1
        logging.debug(f"Processing asset {stats['processed']}/{total - resume_from}: {asset_uuid}")

        success, message = process_asset(service=service, asset_uuid=asset_uuid, old_bestek=old_bestek, new_bestek=new_bestek, transition_dt=transition_dt, dry_run=dry_run)

        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1
            stats["errors"].append({"index": idx, "uuid": asset_uuid, "error": message})

        if stats["processed"] % 10 == 0:
            logging.info(f"Progress: {stats['processed']}/{total - resume_from} (success: {stats['success']}, failed: {stats['failed']})")

    return stats


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    log_file = args.log_dir / f"{Path(__file__).stem}.log"
    setup_logging(log_file)
    logging.info("=" * 60)
    logging.info("Bestekkoppeling Migration Started")
    logging.info("=" * 60)
    logging.info(f"Log file: {log_file}")
    logging.info(f"Arguments: {vars(args)}")

    try:
        try:
            transition_dt = datetime.fromisoformat(args.transition_date)
        except ValueError as exc:
            raise ConfigurationError(f"Invalid transition date format: '{args.transition_date}'. Use ISO format YYYY-MM-DD.") from exc

        df_assets = load_excel_assets(args.excel, args.sheet_name)

        env = Environment[args.env]
        logging.info(f"Initializing EMInfra client for environment: {env.name}")

        client = EMInfraClient(auth_type=AuthType.JWT, env=env, settings_path=args.config_path)
        service = EMInfraService(client)

        stats = run_migration(df_assets=df_assets, service=service, old_bestek=args.old_bestek, new_bestek=args.new_bestek, transition_dt=transition_dt, dry_run=args.dry_run, resume_from=args.resume_from)

        logging.info("=" * 60)
        logging.info("Migration Summary")
        logging.info("=" * 60)
        logging.info(f"Total assets:     {stats['total']}")
        logging.info(f"Skipped (resume): {stats['skipped']}")
        logging.info(f"Processed:        {stats['processed']}")
        logging.info(f"Successful:       {stats['success']}")
        logging.info(f"Failed:           {stats['failed']}")

        if stats["errors"]:
            logging.info("Failed assets:")
            for err in stats["errors"]:
                logging.info(f"  Index {err['index']}: {err['uuid']} - {err['error']}")

        if stats["failed"] > 0 and not args.dry_run:
            logging.error("Migration completed with failures.")
            return 1

        logging.info("Migration completed successfully.")
        return 0

    except ConfigurationError as exc:
        logging.error(f"Configuration error: {exc}")
        return 1
    except FileNotFoundError as exc:
        logging.error(f"File not found: {exc}")
        return 1
    except Exception as exc:
        logging.exception(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
