"""
Sharepoint Client for Microsoft Graph API Integration

This module provides a client for interacting with Microsoft SharePoint through the Graph API.
It handles authentication using MSAL (Microsoft Authentication Library) with client credentials flow
and provides methods for common SharePoint operations like listing files and folders.

Notes:
- Uses OAuth 2.0 client credentials flow (app-only authentication)
- Requires MSAL and requests libraries
- Designed for Azure AD registered applications with site access
"""

import logging
import json
import time
from pathlib import Path

import msal
import requests

from API.settings_loader import load_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class SharepointClient:
    """
    Client for interacting with Microsoft SharePoint via the Graph API.

    This client handles authentication via MSAL client credentials flow and provides
    methods for listing files and folders in a SharePoint site.

    Attributes:
        client_id (str): Azure AD application client ID
        tenant_id (str): Azure AD tenant ID
        client_secret (str): Azure AD application client secret
        site_url (str): SharePoint site URL
        scopes (list): OAuth scopes required for SharePoint access
        app (ConfidentialClientApplication): MSAL application instance
    """

    def __init__(
        self,
        client_id: str,
        tenant_id: str,
        site_url: str,
        client_secret: str = None,
        scopes: list = None,
        token_file: Path = None,
        use_client_credentials: bool = True,
    ):
        """
        Initialize the SharePoint client.

        Args:
            client_id: Azure AD application client ID
            tenant_id: Azure AD tenant ID
            site_url: SharePoint site URL (required for site operations)
            client_secret: Azure AD application client secret (required for client credentials flow)
            scopes: OAuth scopes required for SharePoint access
            token_file: Path to store/load persisted token (for user-delegated auth)
            use_client_credentials: If True, use app-only client credentials flow.
                                   If False, use interactive user-delegated flow with token persistence.

        Attributes:
            client_id (str): Azure AD application client ID
            tenant_id (str): Azure AD tenant ID
            client_secret (str): Azure AD application client secret
            site_url (str): SharePoint site URL
            scopes (list): OAuth scopes required for SharePoint access
            token_file (Path): Path for token persistence (user-delegated mode)
            use_client_credentials (bool): Authentication mode flag
            app (ConfidentialClientApplication): MSAL application instance (client credentials mode)
        """
        if not site_url:
            raise ValueError("site_url is required for SharepointClient operations")

        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret
        self.site_url = site_url.rstrip('/')
        self.scopes = scopes or ["https://graph.microsoft.com/.default"]
        self.token_file = Path(token_file) if token_file else None
        self.use_client_credentials = use_client_credentials

        authority = f"https://login.microsoftonline.com/{tenant_id}"

        if use_client_credentials:
            if not client_secret:
                raise ValueError("client_secret is required for client credentials flow")
            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret,
            )
        else:
            self.app = msal.PublicClientApplication(
                self.client_id,
                authority=authority,
            )
        # Extract the parent site URL (up to /sites/<site_name>)
        # The site_url might be a subsite, but we need the parent site for Graph API access
        parts = self.site_url.split("/sites/")
        if len(parts) > 1:
            # Reconstruct parent site: https://hostname/sites/<first_path_segment>
            path_parts = parts[1].split("/")
            if len(path_parts) > 1:
                # This is a subsite, use the parent site
                self.parent_site_url = f"{parts[0]}/sites/{path_parts[0]}"
                self.subsite_path = parts[1]  # Full path after /sites/
            else:
                self.parent_site_url = self.site_url
                self.subsite_path = None
        else:
            self.parent_site_url = self.site_url
            self.subsite_path = None

    def get_access_token(self) -> str:
        """Get an access token using client credentials flow."""
        result = self.app.acquire_token_for_client(scopes=self.scopes)
        if "access_token" not in result:
            raise RuntimeError(f"Token fout: {result.get('error_description')}")
        return result["access_token"]

    def _get_headers(self) -> dict:
        """Get headers with authorization token."""
        return {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json",
        }

    def _get_site_id(self) -> str:
        """
        Get the site ID from the parent site URL.
        
        The Graph API expects the site path in the format:
        hostname:/sites/path
        """
        headers = self._get_headers()
        site_path = self.parent_site_url.split("https://")[-1]
        # Convert to colon format: hostname:/sites/path
        colon_format = site_path.replace("/sites/", ":/sites/")
        url = f"https://graph.microsoft.com/v1.0/sites/{colon_format}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Fout bij ophalen site: {resp.status_code} - {resp.text}")
        return resp.json()["id"]

    def list_document_libraries(self):
        """List all document libraries in the SharePoint site."""
        site_id = self._get_site_id()
        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            items = resp.json().get("value", [])
            print("📂 Document libraries in SharePoint site:")
            for item in items:
                print(f"- {item.get('name', '(default)')} (id: {item['id']})")
        else:
            print(f"Fout {resp.status_code}: {resp.text}")

    def list_library_items(self, document_library_id: str):
        """List files/folders in a specific document library."""
        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/root/children"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            items = resp.json().get("value", [])
            print(f"📂 Items in document library {document_library_id}:")
            for item in items:
                soort = "Map" if "folder" in item else "Bestand"
                print(f"- {item['name']} ({soort})")
        else:
            print(f"Fout {resp.status_code}: {resp.text}")

    def list_root_items(self, document_library_id: str = None):
        """
        List files/folders in the root of the SharePoint site.
        
        Args:
            document_library_id: Optional document library ID. If not provided, lists items from all document libraries.
        """
        site_id = self._get_site_id()
        headers = self._get_headers()
        
        if document_library_id:
            url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/root/children"
            resp = requests.get(url, headers=headers)
        else:
            # List all document libraries and their contents
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                libraries = resp.json().get("value", [])
                for library in libraries:
                    library_name = library.get("name", "(default)")
                    library_id = library.get("id")
                    print(f"\n📂 Document Library: {library_name}")
                    library_url = f"https://graph.microsoft.com/v1.0/drives/{library_id}/root/children"
                    library_resp = requests.get(library_url, headers=headers)
                    if library_resp.status_code == 200:
                        items = library_resp.json().get("value", [])
                        for item in items:
                            soort = "Map" if "folder" in item else "Bestand"
                            print(f"  - {item['name']} ({soort})")
                    else:
                        print(f"  Fout {library_resp.status_code}: {library_resp.text}")
                return
            else:
                print(f"Fout {resp.status_code}: {resp.text}")
                return
        
        if resp.status_code == 200:
            items = resp.json().get("value", [])
            print("📂 Items in SharePoint root:")
            for item in items:
                soort = "Map" if "folder" in item else "Bestand"
                print(f"- {item['name']} ({soort})")
        else:
            print(f"Fout {resp.status_code}: {resp.text}")

    def get_document_library_by_name(self, library_name: str) -> dict:
        """
        Get a document library by name from the SharePoint site.

        Args:
            library_name: Name of the document library to find

        Returns:
            Document library object if found, None otherwise
        """
        site_id = self._get_site_id()
        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            items = resp.json().get("value", [])
            for item in items:
                if item.get("name") == library_name:
                    return item
        return None

    # ---------- Folder Resolution & Creation ----------

    def _get_or_create_folder(
        self,
        parent_id: str,
        folder_name: str,
        document_library_id: str = None,
    ) -> dict:
        """
        Find an existing folder by name under a parent, or create it if missing.

        Args:
            parent_id: The parent folder/item ID (or 'root' for document library root)
            folder_name: Name of the folder to find or create
            document_library_id: Document library ID. If not provided, uses the default document library.

        Returns:
            Folder item dict with 'id', 'name', 'folder' properties.
        """
        if document_library_id is None:
            document_library_id = self._get_default_document_library_id()

        headers = self._get_headers()

        # First, try to find existing folder
        if parent_id == "root":
            url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/root/children"
        else:
            url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/items/{parent_id}/children"

        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            items = resp.json().get("value", [])
            for item in items:
                if item.get("name") == folder_name and "folder" in item:
                    return item

        # Not found, create it
        if parent_id == "root":
            create_url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/root/children"
        else:
            create_url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/items/{parent_id}/children"

        create_payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename",
        }
        resp = requests.post(create_url, headers=headers, json=create_payload)
        if resp.status_code in {200, 201}:
            return resp.json()
        else:
            raise RuntimeError(f"Failed to create folder '{folder_name}': {resp.status_code} - {resp.text}")

    def _get_or_create_folder_path(
        self,
        folder_path: str,
        document_library_id: str = None,
    ) -> dict:
        """
        Resolve a nested folder path, creating missing parent folders.

        Given a path like 'RSA/RSA_OneDrive', walk segments and create each
        missing parent folder, returning the final folder identifier.

        Args:
            folder_path: Relative path like 'FolderA/FolderB/FolderC'
            document_library_id: Document library ID. If not provided, uses the default.

        Returns:
            Final folder item dict.
        """
        segments = [seg for seg in folder_path.strip("/").split("/") if seg]
        if not segments:
            raise ValueError("folder_path must not be empty")

        current_parent = "root"
        final_folder = None

        for segment in segments:
            final_folder = self._get_or_create_folder(current_parent, segment, document_library_id)
            current_parent = final_folder["id"]

        return final_folder

    def _get_default_document_library_id(self) -> str:
        """Get the default document library ID for the site."""
        site_id = self._get_site_id()
        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()["id"]
        raise RuntimeError(f"Failed to get default document library: {resp.status_code} - {resp.text}")

    # ---------- Token persistence ----------

    def _save_token(self, token_data: dict, token_file: Path) -> None:
        """Save token data to a JSON file."""
        with token_file.open("w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)

    # ---------- Authentication ----------

    @classmethod
    def login_only(
        cls,
        client_id: str,
        tenant_id: str,
        scopes: list = None,
        token_file: Path = None,
    ) -> "SharepointClient":
        """
        Perform interactive browser login and persist token for future sessions.

        Use this classmethod when you only need to obtain and store a token — no
        SharePoint site is accessed, so no `site_url` is required. Later, construct
        a regular SharepointClient with a `site_url` and call `_load_credentials()`
        to silently reuse the persisted token.

        Args:
            client_id: Azure AD application client ID
            tenant_id: Azure AD tenant ID
            scopes: OAuth scopes required for SharePoint access
            token_file: Path to store the token. Defaults to 'sharepoint_token.json'.

        Returns:
            A SharepointClient instance configured for user-delegated auth with the
            persisted token loaded.

        Raises:
            RuntimeError: If login fails.
        """
        if token_file is None:
            token_file = Path("sharepoint_token.json")
        token_file = Path(token_file)

        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.PublicClientApplication(
            client_id,
            authority=authority,
        )

        result = app.acquire_token_interactive(
            scopes=scopes or ["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in result:
            raise RuntimeError(f"Login fout: {result.get('error_description')}")

        result["expires_at"] = time.time() + result.get("expires_in", 3600)
        with token_file.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        logging.info(f"Token opgeslagen in {token_file.resolve()}")

        return result["access_token"]

    def first_login(self, token_file: Path = None) -> str:
        """
        Perform interactive login via browser and persist token for future sessions.

        Convenience wrapper around `SharepointClient.login_only` using this instance's
        client_id, tenant_id and scopes.

        Args:
            token_file: Path to store the token. Defaults to 'sharepoint_token.json'.

        Returns:
            The access token string.

        Raises:
            RuntimeError: If login fails.
        """
        return SharepointClient.login_only(
            client_id=self.client_id,
            tenant_id=self.tenant_id,
            scopes=self.scopes,
            token_file=token_file,
        )

    def _load_credentials(self, token_file: Path = None) -> dict:
        """
        Load stored credential/token, detect expiry, and refresh automatically using refresh token.

        Args:
            token_file: Path to the token file. Defaults to 'sharepoint_token.json'.

        Returns:
            Token data dictionary with access_token, or empty dict if not found and login required.
        """
        if token_file is None:
            token_file = Path("sharepoint_token.json")
        token_file = Path(token_file)

        if not token_file.exists():
            return {}

        with token_file.open("r", encoding="utf-8") as f:
            token_data = json.load(f)

        expires_at = token_data.get("expires_at", 0)
        if time.time() > expires_at - 60:
            logging.info("Token verlopen of bijna verlopen, verversen...")
            refreshed = self._refresh_token(token_data, token_file)
            if refreshed:
                token_data = refreshed
            else:
                return {}

        return token_data

    def _refresh_token(self, token_data: dict, token_file: Path) -> dict:
        """
        Refresh the access token using a refresh token.

        Args:
            token_data: Current token data containing refresh_token.
            token_file: Path to save the refreshed token.

        Returns:
            Refreshed token data, or empty dict if refresh failed.
        """
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.PublicClientApplication(
            self.client_id,
            authority=authority,
        )

        refreshed = app.acquire_token_by_refresh_token(
            token_data.get("refresh_token"),
            self.scopes
        )

        if "access_token" in refreshed:
            refreshed["expires_at"] = time.time() + refreshed.get("expires_in", 3600)
            self._save_token(refreshed, token_file)
            return refreshed
        else:
            logging.warning(f"Kon token niet verversen: {refreshed.get('error_description')}")
            return {}

    def _build_service(self, token_file: Path = None) -> requests.Session:
        """
        Construct an authenticated Microsoft Graph API HTTP session from persisted token.

        Args:
            token_file: Path to the token file. Defaults to 'sharepoint_token.json'.

        Returns:
            A requests.Session with Authorization header set.

        Raises:
            RuntimeError: If no valid token is available.
        """
        token_data = self._load_credentials(token_file)
        if not token_data or "access_token" not in token_data:
            raise RuntimeError("Geen geldige token beschikbaar. Eerst inloggen met first_login().")

        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {token_data['access_token']}",
            "Content-Type": "application/json",
        })
        return session


if __name__ == "__main__":
    import os

    settings = load_settings("settings.json")

    client = SharepointClient(
        client_id=os.getenv("CLIENT_ID"),
        tenant_id=os.getenv("TENANT_ID"),
        client_secret=os.getenv("SECRET"),
        site_url=settings["sharepoint"]["site_url"],
    )

    print("=== Test access ===")
    try:
        token = client.get_access_token()
        print(f"Token length: {len(token)}")
    except Exception as e:
        print(f"Token error: {e}")

    print("\n=== List drives ===")
    client.list_drives()

    print("\n=== List root files (default drive) ===")
    client.list_root_files()