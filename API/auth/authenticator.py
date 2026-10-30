"""AWV Application Authenticator - handles authentication for all AWV services."""
from typing import Optional

from API.auth.enums import AuthType, Environment


class AWVAppAuthenticator:
    """
    Authenticator for AWV applications.
    
    Handles authentication configuration and creates requesters/clients for different services.
    Config files are looked up in standard locations (config/ folder next to cwd, etc.)
    
    Usage:
        auth = AWVAppAuthenticator(env=Environment.PRD, auth_type=AuthType.COOKIE)
        client = auth.eminfra()
        # or
        client = auth.sngateway()
    """
    
    def __init__(
        self,
        env: Environment,
        auth_type: AuthType,
        cookie: str = None,
        settings_filename: str = None,
        **kwargs
    ):
        """
        Initialize authenticator.
        
        Args:
            env: Environment (PRD, DEV, TEI, AIM)
            auth_type: Authentication type (JWT, CERT, COOKIE)
            cookie: Cookie value for COOKIE auth (if not in settings)
            settings_filename: Name of settings file to look for
        """
        self.env = env
        self.auth_type = auth_type
        self.cookie = cookie
        self.settings_filename = settings_filename or "settings_AWV_applications.json"
        self._kwargs = kwargs
        self._requester = None
    
    def create_requester(self, service_path: str = ""):
        """
        Create a requester for a service.
        
        Args:
            service_path: Optional service path to append to base URL
        """
        from API.auth.factory import RequesterFactory
        requester = RequesterFactory.create_requester(
            auth_type=self.auth_type,
            env=self.env,
            cookie=self.cookie,
            settings_filename=self.settings_filename,
            authenticator=self,
            **self._kwargs
        )
        if service_path:
            requester.first_part_url += service_path
        return requester
    
    def get_requester(self):
        """Get or create cached requester."""
        if self._requester is None:
            self._requester = self.create_requester()
        return self._requester
    
    def eminfra(self, **kwargs):
        """Create EMInfra client."""
        from API.clients.eminfra.EMInfraClient import EMInfraClient
        merged_kwargs = {**self._kwargs, **kwargs}
        return EMInfraClient(authenticator=self, **merged_kwargs)
    
    def sngateway(self, **kwargs):
        """Create ServiceNow Gateway client."""
        from API.SNGatewayClient import SNGatewayClient
        merged_kwargs = {**self._kwargs, **kwargs}
        return SNGatewayClient(authenticator=self, **merged_kwargs)
    
    def emson(self, **kwargs):
        """Create EMSON client."""
        from API.EMSONClient import EMSONClient
        merged_kwargs = {**self._kwargs, **kwargs}
        return EMSONClient(authenticator=self, **merged_kwargs)
    
    def locatieservices2(self, **kwargs):
        """Create Locatieservices2 client."""
        from API.Locatieservices2Client import Locatieservices2Client
        merged_kwargs = {**self._kwargs, **kwargs}
        return Locatieservices2Client(authenticator=self, **merged_kwargs)
    
    def fs(self, **kwargs):
        """Create FS client."""
        from API.FSClient import FSClient
        merged_kwargs = {**self._kwargs, **kwargs}
        return FSClient(authenticator=self, **merged_kwargs)
    
    def onedrive(self, **kwargs):
        """Create OneDrive client."""
        from API.OneDriveClient import OneDriveClient
        merged_kwargs = {**self._kwargs, **kwargs}
        return OneDriveClient(authenticator=self, **merged_kwargs)
