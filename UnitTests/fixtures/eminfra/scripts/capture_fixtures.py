#!/usr/bin/env python3
"""
Fixture capture script - hit TEI/DEV (non-prod) to record real API responses.

WARNING: Only use with non-production environments (TEI/DEV).
Never hit production. Scramble/sanitize all data before committing fixtures.
"""
import json
import sys
from pathlib import Path


def main():
    print("This script is a template. Configure with TEI/DEV credentials/settings.")
    print("Steps:")
    print("1. Use AWVAppAuthenticator/EMInfraClient with TEI/DEV environment")
    print("2. Call endpoints to capture responses")
    print("3. Save raw responses to UnitTests/fixtures/eminfra/raw/ (gitignored)")
    print("4. Run sanitize_fixtures.py to sanitize before committing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
