"""AWV API service clients."""
from API.clients.eminfra import EMInfraClient
from API.clients.sngateway import SNGatewayClient
from API.clients.emson import EMSONClient
from API.clients.locatieservices2 import Locatieservices2Client
from API.clients.fs import FSClient
from API.clients.onedrive import OneDriveClient
from API.clients.sharepoint import SharepointClient

__all__ = [
    'EMInfraClient', 'SNGatewayClient', 'EMSONClient',
    'Locatieservices2Client', 'FSClient', 'OneDriveClient', 'SharepointClient'
]
