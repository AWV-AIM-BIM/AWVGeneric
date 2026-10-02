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
        client_secret: str,
        site_url: str,
        scopes: list = None,
    ):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret
        self.site_url = site_url.rstrip('/')
        self.scopes = scopes or ["https://graph.microsoft.com/.default"]
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret,
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

    def list_drives(self):
        """List all drives in the SharePoint site."""
        site_id = self._get_site_id()
        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            items = resp.json().get("value", [])
            print("📂 Drives in SharePoint site:")
            for item in items:
                print(f"- {item.get('name', '(default)')} (id: {item['id']})")
        else:
            print(f"Fout {resp.status_code}: {resp.text}")

    def list_drive_files(self, drive_id: str):
        """List files/folders in a specific drive."""
        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            items = resp.json().get("value", [])
            print(f"📂 Bestanden in drive {drive_id}:")
            for item in items:
                soort = "Map" if "folder" in item else "Bestand"
                print(f"- {item['name']} ({soort})")
        else:
            print(f"Fout {resp.status_code}: {resp.text}")

    def list_root_files(self, drive_id: str = None):
        """
        List files/folders in the root of the SharePoint site.
        
        Args:
            drive_id: Optional drive ID. If not provided, lists files from all drives.
        """
        site_id = self._get_site_id()
        headers = self._get_headers()
        
        if drive_id:
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
            resp = requests.get(url, headers=headers)
        else:
            # List all drives and their contents
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                drives = resp.json().get("value", [])
                for drive in drives:
                    drive_name = drive.get("name", "(default)")
                    drive_id = drive.get("id")
                    print(f"\n📂 Drive: {drive_name}")
                    drive_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
                    drive_resp = requests.get(drive_url, headers=headers)
                    if drive_resp.status_code == 200:
                        items = drive_resp.json().get("value", [])
                        for item in items:
                            soort = "Map" if "folder" in item else "Bestand"
                            print(f"  - {item['name']} ({soort})")
                    else:
                        print(f"  Fout {drive_resp.status_code}: {drive_resp.text}")
                return
            else:
                print(f"Fout {resp.status_code}: {resp.text}")
                return
        
        if resp.status_code == 200:
            items = resp.json().get("value", [])
            print("📂 Bestanden in SharePoint-root:")
            for item in items:
                soort = "Map" if "folder" in item else "Bestand"
                print(f"- {item['name']} ({soort})")
        else:
            print(f"Fout {resp.status_code}: {resp.text}")

    def get_drive_by_name(self, drive_name: str) -> dict:
        """
        Get a drive by name from the SharePoint site.
        
        Args:
            drive_name: Name of the drive to find
            
        Returns:
            Drive object if found, None otherwise
        """
        site_id = self._get_site_id()
        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            items = resp.json().get("value", [])
            for item in items:
                if item.get("name") == drive_name:
                    return item
        return None


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