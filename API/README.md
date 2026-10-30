# AWV API Client Library

A vendorable API client library for AWV services.

## Quick Start

```python
from API import AWVAppAuthenticator
from API.Enums import AuthType, Environment

auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE)
client = auth.eminfra()

# Or instantiate clients directly
from API import EMInfraClient
client = EMInfraClient(authenticator=auth)
```

## Structure

```
API/
├── README.md           # This file
├── __init__.py         # Main exports (backward compatible)
├── auth/               # Authentication & configuration
│   ├── authenticator.py
│   ├── factory.py
│   ├── requester.py
│   ├── jwt.py, cert.py, cookie.py
│   └── settings.py
├── clients/            # Service clients
│   ├── eminfra/        # EMInfra with all services
│   ├── sngateway.py
│   ├── emson.py
│   └── ...
└── samples/            # Example configuration files
    ├── settings_AWV_applications_example.json
    └── settings_sharepoint_example.json
```

## Configuration

Place your `settings_AWV_applications.json` in a `config/` folder next to where you run your code, or in the current directory. The library will search automatically.

See `samples/` for example configurations.

## Vendoring

Just copy the entire `API/` folder to your project. All imports use `API.*` and will work as-is.
