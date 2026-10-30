# API Module - Quick Reference for AI Agents

## Purpose
Vendorable API client library for AWV services (EMInfra, ServiceNow Gateway, SharePoint, etc.).

## Quick Usage

```python
# Recommended: Authenticator pattern
from API import AWVAppAuthenticator
from API.auth.enums import AuthType, Environment

auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE)
client = auth.eminfra()
# client.asset_service, client.bestek_service, etc.

# Alternative: Direct instantiation
from API.clients.eminfra import EMInfraClient
client = EMInfraClient(authenticator=auth)
```

## Structure
- `auth/` - Authentication, requesters, config finding
- `clients/` - Service clients (eminfra has sub-services)
- `samples/` - Example configs
- Config in `../config/` (one level above repo)

## Available Clients
- `auth.eminfra()` / `clients.eminfra.EMInfraClient` - Main EMInfra API
- `auth.sngateway()` / `clients.sngateway.SNGatewayClient`
- `auth.emson()` / `clients.emson.EMSONClient`
- `auth.locatieservices2()` / `clients.locatieservices2.Locatieservices2Client`
- `auth.fs()` / `clients.fs.FSClient`
- `auth.onedrive()` / `clients.onedrive.OneDriveClient`
- `clients.sharepoint.SharepointClient`

## Auth Types
- `AuthType.JWT` - JWT with key files
- `AuthType.CERT` - Certificate auth
- `AuthType.COOKIE` - Cookie auth

## Environments
- `Environment.PRD`, `Environment.DEV`, `Environment.TEI`, `Environment.AIM`

## Notes
- Lazy imports prevent loading heavy deps (JWT/crypto only when needed)
- Settings auto-discovered in `../config/` or `config/`
- Backward compatible imports work
