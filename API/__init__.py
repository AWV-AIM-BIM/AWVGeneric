"""
AWV API Client Library

Quick start:
    from API import AWVAppAuthenticator
    from API.auth.enums import AuthType, Environment
    auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE)
    client = auth.eminfra()
"""
from API.auth import *
from API.clients import *
from API.auth.authenticator import AWVAppAuthenticator
from API.auth.factory import RequesterFactory
from API.auth.settings import load_settings, find_settings_file, resolve_settings_path
from API.auth.enums import AuthType, Environment
from API.clients.eminfra import EMInfraClient

__all__ = [
    'AWVAppAuthenticator', 'RequesterFactory', 
    'load_settings', 'find_settings_file', 'resolve_settings_path',
    'AuthType', 'Environment',
    'EMInfraClient', 'SNGatewayClient', 'EMSONClient',
    'Locatieservices2Client', 'FSClient', 'OneDriveClient', 'SharepointClient'
]
