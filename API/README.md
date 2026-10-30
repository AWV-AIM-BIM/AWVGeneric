# AWV API Client Library

A vendorable API client library for AWV services.

## Quick Start

```python
from API import AWVAppAuthenticator
from API.auth.enums import AuthType, Environment

auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE)
client = auth.eminfra()

# Or instantiate clients directly
from API.clients.eminfra import EMInfraClient
client = EMInfraClient(authenticator=auth)
```

## Structure

```
API/
├── README.md           # This file
├── AGENTS.md           # Quick reference for AI agents
├── __init__.py         # Main exports (backward compatible)
├── auth/               # Authentication & configuration
│   ├── authenticator.py
│   ├── factory.py
│   ├── abstract_requester.py
│   ├── jwt.py, cert.py, cookie.py
│   └── settings.py
├── clients/            # Service clients
│   ├── eminfra/        # EMInfra package with all services
│   ├── eminfra.py      # EMInfra re-export (discoverable)
│   ├── sngateway.py
│   ├── emson.py
│   ├── locatieservices2.py
│   ├── fs.py
│   ├── onedrive.py
│   └── sharepoint.py
└── samples/            # Example configuration files
    ├── settings_AWV_applications_example.json
    └── settings_sharepoint_example.json
```

## Configuration

Place your `settings_AWV_applications.json` in a `config/` folder **one level above** the repository/folder where you copied the `API/` folder to. The library will search automatically starting from the current working directory.

### Example structure when vendoring

```
parent_folder/             # One level above repo
├── config/                # Config folder - OUTSIDE the repo
│   ├── settings_AWV_applications.json
│   ├── settings_sharepoint.json
│   └── private_keys/
└── your_project/          # Your repo (run your code from here)
    ├── API/               # Copied API library
    │   ├── auth/
    │   ├── clients/
    │   ├── samples/
    │   └── ...
    └── your_script.py
```

### Example structure when using in this repo

```
PycharmProjects/           # One level above repo
├── config/                # Config folder - OUTSIDE the repo
│   ├── settings_AWV_applications.json
│   └── private_keys/
└── AWVGeneric/            # Repo root (run your code from here)
    ├── API/               # Library
    └── UseCases/
```

The finder searches up from the current working directory, so running from inside the repo will find `../config/`. 

**For AI agents:** See [AGENTS.md](AGENTS.md) for a quick reference.

See `samples/` for example configurations.

## Vendoring

Just copy the entire `API/` folder to your project. All imports use `API.*` and will work as-is.
