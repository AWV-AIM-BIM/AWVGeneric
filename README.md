# AWVGeneric

Python SDK / automation framework for the Flemish road infrastructure agency (AWV).
Interact with EM-Infra (OTL asset management), Davie, ServiceNow Gateway, OneDrive, and more.

## Prerequisites

- **Python 3.14** (or newer)
- **uv** — fast Python package manager and runner

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:

```bash
uv --version
python3 --version   # should show Python 3.14.x
```

## Setup

```bash
# Create a virtual environment with Python 3.14
uv venv --python 3.14

# Install the project in editable mode (includes dev/test deps)
uv pip install -e ".[dev]"
```

If Python 3.14 is not available locally, uv can download and manage it automatically:

```bash
uv python install 3.14
uv venv --python 3.14
uv pip install -e ".[dev]"
```

## Configuration

Create a `settings.json` in the project root (do **not** commit this file). It should contain authentication credentials for the environments you use:

```json
{
  "authentication": {
    "JWT": {
      "prd": {
        "key_path": "/path/to/private.key",
        "client_id": "your-client-id"
      },
      "dev": {
        "key_path": "/path/to/private.key",
        "client_id": "your-client-id"
      }
    },
    "CERT": {
      "prd": {
        "cert_path": "/path/to/cert.pem",
        "key_path": "/path/to/key.pem"
      }
    }
  },
  "azure": {
    "client_id": "your-azure-client-id"
  },
  "files": {
    "token_file": "token_onedrive.json"
  }
}
```

## Running scripts

Use `uv run` so the virtual environment is activated automatically:

```bash
# Test EM-Infra connectivity
uv run python main_test.py

# Run unit tests
uv run pytest

# Run a specific use-case script
uv run python UseCases/Asset/main_asset_search.py
```

## Linting

```bash
uv run ruff check API/ utils/ UseCases/
```

## Project structure

```
AWVGeneric/
├── API/                    # HTTP clients, auth, domain models, services
│   ├── AbstractRequester.py
│   ├── RequesterFactory.py
│   ├── Enums.py
│   ├── CookieRequester.py
│   ├── JWTRequester.py
│   ├── CertRequester.py
│   ├── EMSONClient.py
│   ├── SNGatewayClient.py
│   ├── OneDriveClient.py
│   ├── Locatieservices2Client.py
│   ├── FSClient.py
│   ├── settings_loader.py
│   └── eminfra/            # EM-Infra domain models + 17 service classes
├── utils/                  # Shared helpers (dates, WKT, EAN, queries, spatial)
├── UseCases/               # Business logic / operational scripts
├── Generic/                # Excel utilities
├── Exceptions/             # Custom exceptions
├── UnitTests/              # Pytest tests
├── main_test.py            # Quick connectivity test
├── report_davie_aanleveringen.py
├── CodingAgents/
│   ├── ai.md               # Agent workflow instructions
│   └── PROJECT.md          # Detailed project documentation
├── pyproject.toml          # Project metadata + dependencies
└── requirements.txt        # Legacy flat requirements
```

## Notes

- The project assumes a Linux environment; some scripts contain Windows-specific paths.
- `settings.json` is git-ignored and must be created locally.
- `report_davie_aanleveringen.py` duplicates some `API/` classes for historical reasons; prefer using `API/` directly.
