#!/usr/bin/env python3
"""
Data sanitization script - scramble PII, hash/replace names/emails, remap UUIDs consistently.
"""
import json
import hashlib
import sys
from pathlib import Path
from typing import Any, Dict


def consistent_uuid(uuid: str, mapping: Dict[str, str]) -> str:
    if not uuid or uuid in mapping:
        return mapping.get(uuid, uuid)
    # Generate deterministic fake UUID
    h = hashlib.sha256(uuid.encode()).hexdigest()
    fake = f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
    mapping[uuid] = fake
    return fake


def sanitize_value(value: Any, mapping: Dict[str, str], path: str = "") -> Any:
    if isinstance(value, str):
        # Remap UUIDs
        if len(value) == 36 and value.count("-") == 4:
            return consistent_uuid(value, mapping)
        # Hash emails
        if "@" in value and "." in value:
            h = hashlib.sha256(value.encode()).hexdigest()
            return f"user{h[:8]}@example.com"
        # Hash names in certain contexts
        if any(k in path.lower() for k in ["naam", "name", "commentaar", "omschrijving"]):
            if len(value) > 3 and not value.startswith("http"):
                h = hashlib.sha256(value.encode()).hexdigest()
                return f"Sanitized_{h[:12]}"
        return value
    elif isinstance(value, dict):
        return {k: sanitize_value(v, mapping, f"{path}.{k}") for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_value(item, mapping, path) for item in value]
    return value


def main():
    raw_dir = Path(__file__).parent.parent / "raw"
    out_dir = Path(__file__).parent.parent / "sanitized"
    mappings_dir = Path(__file__).parent.parent / "mappings"
    out_dir.mkdir(parents=True, exist_ok=True)
    mappings_dir.mkdir(parents=True, exist_ok=True)

    mapping_file = mappings_dir / "uuid_mapping.json"
    uuid_mapping = {}
    if mapping_file.exists():
        uuid_mapping = json.loads(mapping_file.read_text())

    if not raw_dir.exists():
        print(f"No raw fixtures found in {raw_dir}")
        return 0

    for raw_file in raw_dir.glob("*.json"):
        print(f"Sanitizing {raw_file}")
        data = json.loads(raw_file.read_text())
        sanitized = sanitize_value(data, uuid_mapping)
        out_file = out_dir / raw_file.name
        out_file.write_text(json.dumps(sanitized, indent=2))
        print(f"  -> {out_file}")

    mapping_file.write_text(json.dumps(uuid_mapping, indent=2))
    print(f"UUID mappings saved to {mapping_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
