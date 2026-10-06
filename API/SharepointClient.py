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
from dataclasses import dataclass

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
        items = list(self._list_children("root", document_library_id))
        print(f"📂 Items in document library {document_library_id}:")
        for item in items:
            soort = "Map" if "folder" in item else "Bestand"
            print(f"- {item['name']} ({soort})")

    def list_root_items(self, document_library_id: str = None):
        """
        List files/folders in the root of the SharePoint site.
        
        Args:
            document_library_id: Optional document library ID. If not provided, lists items from all document libraries.
        """
        if document_library_id:
            items = list(self._list_children("root", document_library_id))
            print("📂 Items in SharePoint root:")
            for item in items:
                soort = "Map" if "folder" in item else "Bestand"
                print(f"- {item['name']} ({soort})")
        else:
            # List all document libraries and their contents
            site_id = self._get_site_id()
            headers = self._get_headers()
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                libraries = resp.json().get("value", [])
                for library in libraries:
                    library_name = library.get("name", "(default)")
                    library_id = library.get("id")
                    print(f"\n📂 Document Library: {library_name}")
                    items = list(self._list_children("root", library_id))
                    for item in items:
                        soort = "Map" if "folder" in item else "Bestand"
                        print(f"  - {item['name']} ({soort})")
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

    # ---------- Listing & Lookup ----------

    def _list_children(
        self,
        parent_id: str,
        document_library_id: str = None,
        page_size: int = 200,
    ):
        """
        Enumerate all immediate child items (folders and files) within a given
        parent folder, with pagination.

        Args:
            parent_id: The parent folder/item ID (or 'root' for document library root)
            document_library_id: Document library ID. If not provided, uses the default.
            page_size: Number of items per page (max 999 per Graph API).

        Yields:
            Item dicts for each child (folder or file).
        """
        if document_library_id is None:
            document_library_id = self._get_default_document_library_id()

        headers = self._get_headers()

        if parent_id == "root":
            url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/root/children"
        else:
            url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/items/{parent_id}/children"

        # Add page size parameter
        params = {"$top": page_size}

        while url:
            resp = requests.get(url, headers=headers, params=params)
            params = None  # Only use $top on first request; subsequent pages use @odata.nextLink
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to list children: {resp.status_code} - {resp.text}")

            data = resp.json()
            for item in data.get("value", []):
                yield item

            url = data.get("@odata.nextLink")

    def _find_child_by_name(
        self,
        parent_id: str,
        name: str,
        document_library_id: str = None,
    ) -> dict | None:
        """
        Locate a single child item (file or folder) by name within a parent folder.

        Args:
            parent_id: The parent folder/item ID (or 'root' for document library root)
            name: Name of the child item to find
            document_library_id: Document library ID. If not provided, uses the default.

        Returns:
            Item dict if found, None otherwise.
        """
        for item in self._list_children(parent_id, document_library_id):
            if item.get("name") == name:
                return item
        return None

    # ---------- Temporary File & Skip Filters ----------

    def _is_temporary_workbook(self, filename: str) -> bool:
        """
        Return True for temporary/lock workbook filenames.

        Matches: '_tmp_' suffix, '~$' lock prefix, '.lock' suffix.
        """
        return (
            "_tmp_" in filename
            or filename.startswith("~$")
            or filename.endswith(".lock")
        )

    def _should_skip(self, name: str) -> bool:
        """
        Return True for folder/file names that should never be mirrored.
        """
        return name.lower() in {"archief", "archivedreports", "staged_summaries", "logs"}

    def _is_safe_name(self, name: str) -> bool:
        """
        Validate a safe component name for local filesystem.

        Rejects: empty, '.', '..', names containing '/' or '\\', control characters.
        """
        if not name or name in (".", ".."):
            return False
        if "/" in name or "\\" in name:
            return False
        if any(ord(c) < 32 or ord(c) == 127 for c in name):
            return False
        return True

    def _is_expected_root_folder_name(self, name: str) -> bool:
        """
        Return True for expected root-level folder names.

        Matches 'overzicht' (case-insensitive) or bucket pattern 'NNNN-NNNN'.
        """
        import re
        return name.lower() == "overzicht" or bool(re.match(r"^\d{4}-\d{4}$", name))

    # ---------- Retry & Error Handling ----------

    def _is_retryable_library_error(self, exc: Exception) -> bool:
        """
        Classify an exception as transient/retryable.

        Retryable: timeouts, connection errors, HTTP 408/429/5xx, rate-limit/quota keywords.
        """
        import requests.exceptions as req_exc

        if isinstance(exc, (req_exc.Timeout, req_exc.ConnectionError)):
            return True

        if isinstance(exc, req_exc.HTTPError):
            resp = getattr(exc, "response", None)
            if resp is not None:
                status = resp.status_code
                if status in {408, 429} or 500 <= status < 600:
                    return True
                # Check for rate-limit/quota keywords in response
                try:
                    text = resp.text.lower()
                    if any(kw in text for kw in ("rate limit", "quota", "throttle", "too many requests")):
                        return True
                except Exception:
                    pass

        # Check exception message for rate-limit keywords
        msg = str(exc).lower()
        if any(kw in msg for kw in ("rate limit", "quota", "throttle", "too many requests")):
            return True

        return False

    def _retry_on_library_error(self, func, *args, **kwargs):
        """
        Retry a wrapped API call with exponential backoff.

        Base delay 2s, max delay 120s, max retries 5.
        """
        import time
        import random

        base_delay = 2
        max_delay = 120
        max_retries = 5

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if attempt == max_retries or not self._is_retryable_library_error(exc):
                    raise
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                logging.warning(f"Retryable error (attempt {attempt + 1}/{max_retries}): {exc}. Waiting {delay:.1f}s...")
                time.sleep(delay)

    # ---------- Download (SharePoint → Local Mirror) ----------

    def _clear_local_mirror_target(self, local_folder: Path) -> None:
        """
        Remove all contents of a local folder before downloading,
        while preserving local-only control folders.
        """
        if not local_folder.exists():
            local_folder.mkdir(parents=True, exist_ok=True)
            return

        preserved = {"archief", "archivedreports", "staged_summaries", "logs"}
        for item in local_folder.iterdir():
            if item.name.lower() in preserved:
                continue
            if item.is_dir():
                import shutil
                shutil.rmtree(item)
            else:
                item.unlink()

    def _download_file(
        self,
        item_id: str,
        local_path: Path,
        document_library_id: str = None,
        chunk_size: int = 8192,
    ) -> None:
        """
        Download a single file by its item-id into a local path,
        with resumable/streaming capability.

        Args:
            item_id: Graph item ID of the file
            local_path: Local file path to save to
            document_library_id: Document library ID. If not provided, uses the default.
            chunk_size: Streaming chunk size in bytes
        """
        if document_library_id is None:
            document_library_id = self._get_default_document_library_id()

        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/items/{item_id}/content"

        def _do_download():
            resp = requests.get(url, headers=headers, stream=True)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to download file {item_id}: {resp.status_code} - {resp.text}")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

        self._retry_on_library_error(_do_download)

    def _download_tree(
        self,
        parent_id: str,
        local_folder: Path,
        document_library_id: str = None,
        is_root: bool = True,
        apply_root_filter: bool = False,
    ) -> None:
        """
        Recursively download a folder tree and mirror all files into a local directory.

        Args:
            parent_id: Remote parent folder/item ID (or 'root')
            local_folder: Local directory to mirror into
            document_library_id: Document library ID. If not provided, uses the default.
            is_root: Whether this is the root call (applies root-level filters if apply_root_filter=True)
            apply_root_filter: If True, apply the expected root folder name filter (for structured sync)
        """
        if document_library_id is None:
            document_library_id = self._get_default_document_library_id()

        for item in self._list_children(parent_id, document_library_id):
            name = item.get("name", "")
            if not name:
                continue

            # Skip temporary/lock workbooks
            if self._is_temporary_workbook(name):
                logging.debug(f"Skipping temporary workbook: {name}")
                continue

            # Skip unsafe names
            if not self._is_safe_name(name):
                logging.debug(f"Skipping unsafe name: {name}")
                continue

            # At root level, apply expected folder name filter only if requested
            if is_root and apply_root_filter and not self._is_expected_root_folder_name(name):
                logging.debug(f"Skipping unexpected root folder: {name}")
                continue

            # Skip control folders
            if self._should_skip(name):
                logging.debug(f"Skipping control folder: {name}")
                continue

            local_item_path = local_folder / name

            if "folder" in item:
                # Create the directory for this folder (even if empty)
                local_item_path.mkdir(parents=True, exist_ok=True)
                # Recurse into subfolder
                self._download_tree(item["id"], local_item_path, document_library_id, is_root=False, apply_root_filter=apply_root_filter)
            elif "file" in item:
                # Download file
                logging.info(f"Downloading: {local_item_path}")
                self._download_file(item["id"], local_item_path, document_library_id)

    def sync_library_to_local(
        self,
        remote_folder_path: str,
        local_folder: str | Path,
        document_library_id: str = None,
    ) -> bool:
        """
        Public download mirror: resolve/ensure a remote folder path,
        clear the local mirror target, download the full tree,
        return success/failure.

        Args:
            remote_folder_path: Remote folder path like 'RSA/RSA_OneDrive'.
                               Empty string means the entire document library root.
            local_folder: Local directory to mirror into
            document_library_id: Document library ID. If not provided, uses the default.

        Returns:
            True on success, False on failure.
        """
        try:
            local_path = Path(local_folder)
            self._clear_local_mirror_target(local_path)

            # Resolve/create the remote folder path
            if remote_folder_path and remote_folder_path.strip("/"):
                remote_folder = self._get_or_create_folder_path(remote_folder_path, document_library_id)
                parent_id = remote_folder["id"]
            else:
                # Empty path = entire document library root
                parent_id = "root"

            # Download the tree
            apply_root_filter = bool(remote_folder_path and remote_folder_path.strip("/"))
            self._download_tree(parent_id, local_path, document_library_id, apply_root_filter=apply_root_filter)

            return True
        except Exception as exc:
            logging.error(f"sync_library_to_local failed: {exc}")
            return False

    # ---------- Deletion ----------

    def _delete_library_item_recursive(self, item_id: str, document_library_id: str = None) -> None:
        """
        Delete an item and, if it is a folder, delete all its contents first.

        Args:
            item_id: Graph item ID to delete
            document_library_id: Document library ID. If not provided, uses the default.
        """
        if document_library_id is None:
            document_library_id = self._get_default_document_library_id()

        headers = self._get_headers()
        url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/items/{item_id}"

        def _do_delete():
            # First get the item to check if it's a folder
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to get item {item_id}: {resp.status_code} - {resp.text}")
            item = resp.json()

            # If it's a folder, recursively delete children first
            if "folder" in item:
                children_url = f"{url}/children"
                children_resp = requests.get(children_url, headers=headers)
                if children_resp.status_code == 200:
                    for child in children_resp.json().get("value", []):
                        self._delete_library_item_recursive(child["id"], document_library_id)

            # Delete the item itself
            del_resp = requests.delete(url, headers=headers)
            if del_resp.status_code not in {200, 204}:
                raise RuntimeError(f"Failed to delete item {item_id}: {del_resp.status_code} - {del_resp.text}")

        self._retry_on_library_error(_do_delete)

    # ---------- Upload (Local Mirror → SharePoint) ----------

    def _upload_or_update_file_once(
        self,
        local_path: Path,
        parent_id: str,
        document_library_id: str = None,
    ) -> dict:
        """
        Create a new file or update an existing one in a target folder,
        replacing a conflicting folder with file deletion when names collide.

        Args:
            local_path: Local file path to upload
            parent_id: Remote parent folder ID (or 'root')
            document_library_id: Document library ID. If not provided, uses the default.

        Returns:
            The uploaded/updated item dict.
        """
        if document_library_id is None:
            document_library_id = self._get_default_document_library_id()

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        filename = local_path.name
        headers = self._get_headers()

        # Check for existing item with same name
        existing = self._find_child_by_name(parent_id, filename, document_library_id)

        # If there's a folder with the same name, delete it first
        if existing and "folder" in existing:
            logging.info(f"Removing conflicting folder: {filename}")
            self._delete_drive_item_recursive(existing["id"], document_library_id)
            existing = None

        if existing and "file" in existing:
            # Update existing file
            upload_url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/items/{existing['id']}/content"
            method = "PUT"
        else:
            # Create new file
            if parent_id == "root":
                upload_url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/root:/{filename}:/content"
            else:
                upload_url = f"https://graph.microsoft.com/v1.0/drives/{document_library_id}/items/{parent_id}:/{filename}:/content"
            method = "PUT"

        headers["Content-Type"] = "application/octet-stream"

        def _do_upload():
            with open(local_path, "rb") as f:
                if method == "PUT" and "items/" in upload_url and "/content" in upload_url and ":" not in upload_url.split("items/")[1].split("/")[0]:
                    # Updating existing file by ID
                    resp = requests.put(upload_url, headers=headers, data=f)
                else:
                    # Creating new file using :/path:/content
                    resp = requests.put(upload_url, headers=headers, data=f)

            if resp.status_code not in {200, 201}:
                raise RuntimeError(f"Failed to upload {filename}: {resp.status_code} - {resp.text}")
            return resp.json()

        return self._retry_on_library_error(_do_upload)

    def _upload_or_update_file(
        self,
        local_path: Path,
        parent_id: str,
        document_library_id: str = None,
    ) -> dict:
        """
        Upload or update a single file with retries, building a fresh upload session per attempt.

        Args:
            local_path: Local file path to upload
            parent_id: Remote parent folder ID (or 'root')
            document_library_id: Document library ID. If not provided, uses the default.

        Returns:
            The uploaded/updated item dict.
        """
        return self._retry_on_library_error(
            self._upload_or_update_file_once,
            local_path, parent_id, document_library_id
        )

    def _sync_local_dir_to_library(
        self,
        local_folder: Path,
        parent_id: str,
        document_library_id: str = None,
    ) -> tuple[int, int, int]:
        """
        Recursively sync a local directory tree to a remote folder:
        create missing folders, upload new files, update changed files,
        and delete remote-only files/folders that no longer exist locally.

        Args:
            local_folder: Local directory to sync
            parent_id: Remote parent folder ID (or 'root')
            document_library_id: Document library ID. If not provided, uses the default.

        Returns:
            Tuple of (uploaded_count, updated_count, errors_count)
        """
        if document_library_id is None:
            document_library_id = self._get_default_document_library_id()

        if not local_folder.exists():
            raise FileNotFoundError(f"Local folder not found: {local_folder}")

        uploaded = 0
        updated = 0
        errors = 0

        # Get existing remote items
        remote_items = {item["name"]: item for item in self._list_children(parent_id, document_library_id)}
        local_names = set()

        # Process local files and folders
        for local_item in local_folder.iterdir():
            name = local_item.name
            local_names.add(name)

            if self._should_skip(name) or self._is_temporary_workbook(name) or not self._is_safe_name(name):
                logging.debug(f"Skipping local item: {name}")
                continue

            if local_item.is_dir():
                # Get or create remote folder
                remote_folder = self._get_or_create_folder(parent_id, name, document_library_id)
                # Recurse
                u, up, e = self._sync_local_dir_to_library(local_item, remote_folder["id"], document_library_id)
                uploaded += u
                updated += up
                errors += e
            elif local_item.is_file():
                remote_item = remote_items.get(name)
                try:
                    result = self._upload_or_update_file(local_item, parent_id, document_library_id)
                    if remote_item and "file" in remote_item:
                        updated += 1
                        logging.info(f"Updated: {name}")
                    else:
                        uploaded += 1
                        logging.info(f"Uploaded: {name}")
                except Exception as exc:
                    errors += 1
                    logging.error(f"Failed to upload {name}: {exc}")

        # Delete remote-only items that no longer exist locally
        for name, remote_item in remote_items.items():
            if name not in local_names and not self._should_skip(name):
                try:
                    logging.info(f"Deleting remote-only item: {name}")
                    self._delete_library_item_recursive(remote_item["id"], document_library_id)
                except Exception as exc:
                    errors += 1
                    logging.error(f"Failed to delete remote item {name}: {exc}")

        return uploaded, updated, errors

    def sync_local_to_library(
        self,
        local_folder: str | Path,
        remote_folder_path: str,
        document_library_id: str = None,
    ) -> bool:
        """
        Public upload mirror: authenticate, ensure remote folder path,
        run _sync_local_dir_to_library, log summary, return success/failure.

        Args:
            local_folder: Local directory to sync
            remote_folder_path: Remote folder path like 'RSA/RSA_OneDrive'
            document_library_id: Document library ID. If not provided, uses the default.

        Returns:
            True on success, False on failure.
        """
        try:
            local_path = Path(local_folder)
            if not local_path.exists():
                raise FileNotFoundError(f"Local folder not found: {local_path}")

            # Resolve/create the remote folder path
            if remote_folder_path and remote_folder_path.strip("/"):
                remote_folder = self._get_or_create_folder_path(remote_folder_path, document_library_id)
                parent_id = remote_folder["id"]
            else:
                parent_id = "root"

            # Sync
            uploaded, updated, errors = self._sync_local_dir_to_library(local_path, parent_id, document_library_id)

            logging.info(f"sync_local_to_library summary: uploaded={uploaded}, updated={updated}, errors={errors}")
            return errors == 0
        except Exception as exc:
            logging.error(f"sync_local_to_library failed: {exc}")
            return False

    def upload_folder_to_library(
        self,
        local_folder: str | Path,
        document_library_id: str = None,
        extensions: tuple = (".xlsx",),
    ) -> bool:
        """
        Legacy top-level upload: upload only top-level files matching a set of extensions
        (e.g. .xlsx), skipping root-level files and temporary workbooks.

        Args:
            local_folder: Local directory containing files to upload
            document_library_id: Document library ID. If not provided, uses the default.
            extensions: File extensions to include (default: .xlsx)

        Returns:
            True on success, False on failure.
        """
        try:
            local_path = Path(local_folder)
            if not local_path.exists():
                raise FileNotFoundError(f"Local folder not found: {local_path}")

            if document_library_id is None:
                document_library_id = self._get_default_document_library_id()

            uploaded = 0
            errors = 0

            for local_file in local_path.iterdir():
                if not local_file.is_file():
                    continue
                if local_file.suffix.lower() not in extensions:
                    continue
                if self._is_temporary_workbook(local_file.name):
                    continue

                try:
                    self._upload_or_update_file(local_file, "root", document_library_id)
                    uploaded += 1
                    logging.info(f"Uploaded: {local_file.name}")
                except Exception as exc:
                    errors += 1
                    logging.error(f"Failed to upload {local_file.name}: {exc}")

            logging.info(f"upload_folder_to_library summary: uploaded={uploaded}, errors={errors}")
            return errors == 0
        except Exception as exc:
            logging.error(f"upload_folder_to_library failed: {exc}")
            return False

    # ---------- Local Mirror Validation ----------

    def _discover_expected_buckets(self, local_folder: Path) -> set[str]:
        """
        Scan Reports/ and ArchivedReports/ directories for Report#### files
        to compute the expected set of bucket folder names (0000-0099, etc.).

        Args:
            local_folder: Local mirror root folder

        Returns:
            Set of expected bucket folder names (e.g., {'0000-0099', '0100-0199'})
        """
        import re

        expected = set()
        bucket_pattern = re.compile(r"^(\d{4})-(\d{4})$")

        for subdir in ("Reports", "ArchivedReports"):
            reports_dir = local_folder / subdir
            if not reports_dir.exists():
                continue

            for item in reports_dir.iterdir():
                if item.is_file() and item.name.startswith("Report") and item.name[6:].isdigit():
                    # Extract report number from filename like "Report0042.xlsx"
                    try:
                        report_num = int(item.name[6:10])
                        bucket_start = (report_num // 100) * 100
                        bucket_end = bucket_start + 99
                        bucket_name = f"{bucket_start:04d}-{bucket_end:04d}"
                        expected.add(bucket_name)
                    except (ValueError, IndexError):
                        pass

        return expected

    def validate_local_mirror(self, local_folder: Path) -> tuple[bool, str]:
        """
        Validate local mirror layout.

        Checks that the local mirror contains at minimum:
        - An 'Overzicht' folder (case-insensitive, created if missing)
        - An 'Overzicht/[RSA] Overzicht rapporten.xlsx' workbook
        - A 'logs' folder (created if missing)
        - All expected bucket folders (created if missing)
        - At least one bucket folder

        Args:
            local_folder: Local mirror root folder

        Returns:
            Tuple of (is_valid, reason)
        """
        local_path = Path(local_folder)

        # Ensure Overzicht folder exists
        overzicht_dir = None
        for item in local_path.iterdir():
            if item.is_dir() and item.name.lower() == "overzicht":
                overzicht_dir = item
                break

        if overzicht_dir is None:
            overzicht_dir = local_path / "Overzicht"
            overzicht_dir.mkdir(parents=True, exist_ok=True)
            logging.info("Created missing 'Overzicht' folder")

        # Check for Overzicht workbook
        workbook_found = False
        for item in overzicht_dir.iterdir():
            if item.is_file() and "overzicht" in item.name.lower() and "rapport" in item.name.lower():
                workbook_found = True
                break

        if not workbook_found:
            return False, "Missing '[RSA] Overzicht rapporten.xlsx' in Overzicht folder"

        # Ensure logs folder exists
        logs_dir = local_path / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
            logging.info("Created missing 'logs' folder")

        # Discover and ensure expected bucket folders
        expected_buckets = self._discover_expected_buckets(local_path)
        if not expected_buckets:
            return False, "No expected buckets found (no Report#### files in Reports/ or ArchivedReports/)"

        for bucket in expected_buckets:
            bucket_dir = local_path / bucket
            if not bucket_dir.exists():
                bucket_dir.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created missing bucket folder: {bucket}")

        # Verify at least one bucket folder exists
        existing_buckets = [b for b in expected_buckets if (local_path / b).exists()]
        if not existing_buckets:
            return False, "No bucket folders present in local mirror"

        return True, "Local mirror layout is valid"

    # ---------- Run Log Management ----------

    def write_daily_run_log(
        self,
        local_folder: Path,
        status: str,
    ) -> None:
        """
        Write a dated run log entry.

        Appends a timestamped status line (e.g., POST_RUN_UPLOAD_START,
        POST_RUN_UPLOAD_DONE, POST_RUN_UPLOAD_FAILED) into a
        logs/run_YYYYMMDD.log file inside the local folder.

        Args:
            local_folder: Local mirror root folder
            status: Status string to log
        """
        from datetime import datetime

        local_path = Path(local_folder)
        logs_dir = local_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y%m%d")
        log_file = logs_dir / f"run_{today}.log"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - {status}\n")

    def prune_daily_run_logs(
        self,
        local_folder: Path,
        keep: int = 14,
    ) -> None:
        """
        Prune old daily run logs, keeping only the newest N files.

        Args:
            local_folder: Local mirror root folder
            keep: Number of recent log files to keep (default 14)
        """
        local_path = Path(local_folder)
        logs_dir = local_path / "logs"
        if not logs_dir.exists():
            return

        log_files = sorted(
            logs_dir.glob("run_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_log in log_files[keep:]:
            try:
                old_log.unlink()
                logging.info(f"Pruned old run log: {old_log.name}")
            except Exception as exc:
                logging.warning(f"Failed to prune {old_log.name}: {exc}")

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


# ---------- Microsoft Graph Uploader Abstraction ----------

@dataclass
class GraphUploadTarget:
    """
    Holds a document library ID and folder path identifying a SharePoint/OneDrive destination.
    """
    document_library_id: str
    folder_path: str


class MsGraphUploader:
    """
    Single-file Microsoft Graph uploader.

    Uploads a single local file to a GraphUploadTarget via the Microsoft Graph API.
    """

    def __init__(self, client: "SharepointClient"):
        self.client = client

    def upload_file(
        self,
        local_path: Path,
        target: GraphUploadTarget,
    ) -> dict:
        """
        Upload a single local file to a GraphUploadTarget.

        Args:
            local_path: Local file path to upload
            target: GraphUploadTarget with document_library_id and folder_path

        Returns:
            The uploaded item dict.
        """
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Resolve folder path
        if target.folder_path and target.folder_path.strip("/"):
            remote_folder = self.client._get_or_create_folder_path(
                target.folder_path, target.document_library_id
            )
            parent_id = remote_folder["id"]
        else:
            parent_id = "root"

        return self.client._upload_or_update_file(local_path, parent_id, target.document_library_id)


# ---------- Cross-Module Compatibility ----------

def report_bucket_name(report_number: int) -> str:
    """
    Compute the bucket folder name for a report number.

    Convention: <start>-<end> where start = (n // 100) * 100, end = start + 99
    e.g., report 42 -> '0000-0099', report 157 -> '0100-0199'

    Args:
        report_number: Report number

    Returns:
        Bucket folder name string.
    """
    bucket_start = (report_number // 100) * 100
    bucket_end = bucket_start + 99
    return f"{bucket_start:04d}-{bucket_end:04d}"


def report_sharepoint_url(
    site_url: str,
    document_library_name: str,
    report_number: int,
    filename: str,
) -> str:
    """
    Generate a SharePoint URL for a report workbook.

    Args:
        site_url: SharePoint site URL
        document_library_name: Document library name
        report_number: Report number
        filename: Workbook filename

    Returns:
        SharePoint URL string.
    """
    bucket = report_bucket_name(report_number)
    base = site_url.rstrip("/")
    return f"{base}/{document_library_name}/{bucket}/{filename}"


# ---------- Pipeline State Integration ----------

class DailyLibrarySyncGate:
    """
    External orchestrator polling gate.

    Observes an external pipeline-state store (SQLite) for
    'sharepoint_download' and 'sharepoint_upload' phases/statuses
    to coordinate when report execution may proceed.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def wait_for_download(self, timeout: float = 3600, poll_interval: float = 30) -> bool:
        """
        Wait for sharepoint_download phase to complete.

        Args:
            timeout: Maximum wait time in seconds
            poll_interval: Poll interval in seconds

        Returns:
            True if download completed, False on timeout/error.
        """
        import sqlite3
        import time

        start = time.time()
        while time.time() - start < timeout:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute(
                        "SELECT status FROM pipeline_state WHERE phase = 'sharepoint_download'"
                    ).fetchone()
                    if row and row["status"] == "completed":
                        return True
                    if row and row["status"] == "failed":
                        return False
            except Exception:
                pass
            time.sleep(poll_interval)
        return False

    def wait_for_upload(self, timeout: float = 3600, poll_interval: float = 30) -> bool:
        """
        Wait for sharepoint_upload phase to complete.

        Args:
            timeout: Maximum wait time in seconds
            poll_interval: Poll interval in seconds

        Returns:
            True if upload completed, False on timeout/error.
        """
        import sqlite3
        import time

        start = time.time()
        while time.time() - start < timeout:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute(
                        "SELECT status FROM pipeline_state WHERE phase = 'sharepoint_upload'"
                    ).fetchone()
                    if row and row["status"] == "completed":
                        return True
                    if row and row["status"] == "failed":
                        return False
            except Exception:
                pass
            time.sleep(poll_interval)
        return False


def upload_after_run(
    client: "SharepointClient",
    local_folder: str | Path,
    remote_folder_path: str,
    document_library_id: str,
    db_path: str | Path,
) -> bool:
    """
    Upload-after-run hook for ReportLoopRunner.on_run_complete.

    Sets pipeline-state phase to 'sharepoint_upload', uploads the local mirror
    via sync_local_to_library, and updates pipeline-state to 'completed'
    or 'failed' accordingly.

    Args:
        client: SharepointClient instance
        local_folder: Local mirror path
        remote_folder_path: Remote folder path
        document_library_id: Document library ID
        db_path: SQLite database path for pipeline state

    Returns:
        True on success, False on failure.
    """
    import sqlite3
    from datetime import datetime

    def set_phase(phase: str, status: str):
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pipeline_state (phase, status, updated_at)
                VALUES (?, ?, ?)
                """,
                (phase, status, datetime.now().isoformat()),
            )
            conn.commit()

    set_phase("sharepoint_upload", "in_progress")
    try:
        success = client.sync_local_to_library(local_folder, remote_folder_path, document_library_id)
        set_phase("sharepoint_upload", "completed" if success else "failed")
        return success
    except Exception as exc:
        logging.error(f"upload_after_run failed: {exc}")
        set_phase("sharepoint_upload", "failed")
        return False


# ---------- CLI Interface ----------

def _main():
    """Command-line interface for SharepointClient."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="SharePoint CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common arguments
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--client-id", required=True, help="Azure AD client ID")
    common.add_argument("--tenant-id", required=True, help="Azure AD tenant ID")
    common.add_argument("--site-url", required=True, help="SharePoint site URL")
    common.add_argument("--document-library-id", help="Document library ID (optional, uses default)")
    common.add_argument("--token-file", default="sharepoint_token.json", help="Token file path")

    # login command
    login_parser = subparsers.add_parser("login", parents=[common], help="Perform interactive login and persist token")
    login_parser.add_argument("--client-secret", help="Client secret (optional for device code flow)")

    # sync-down command
    sync_down_parser = subparsers.add_parser("sync-down", parents=[common], help="Mirror SharePoint folder to local folder")
    sync_down_parser.add_argument("--remote-path", default="", help="Remote folder path (empty = entire library)")
    sync_down_parser.add_argument("--local-folder", required=True, help="Local folder to mirror into")

    # sync-up command
    sync_up_parser = subparsers.add_parser("sync-up", parents=[common], help="Mirror local folder to SharePoint folder")
    sync_up_parser.add_argument("--local-folder", required=True, help="Local folder to sync")
    sync_up_parser.add_argument("--remote-path", required=True, help="Remote folder path")

    # upload command
    upload_parser = subparsers.add_parser("upload", parents=[common], help="Legacy top-level file upload")
    upload_parser.add_argument("--local-folder", required=True, help="Local folder containing files")
    upload_parser.add_argument("--extensions", default=".xlsx", help="Comma-separated extensions (e.g., .xlsx,.pdf)")

    args = parser.parse_args()

    # Build client
    if args.command == "login":
        # For login, we don't need site_url or client_secret for device code
        client = SharepointClient(
            client_id=args.client_id,
            tenant_id=args.tenant_id,
            client_secret=args.client_secret or "",
            site_url=args.site_url,
        )
    else:
        client = SharepointClient(
            client_id=args.client_id,
            tenant_id=args.tenant_id,
            client_secret="",  # Will use token file
            site_url=args.site_url,
            use_client_credentials=False,
            token_file=args.token_file,
        )

    try:
        if args.command == "login":
            token = client.first_login(args.token_file)
            print(f"Login successful. Token saved to {args.token_file}")
            return 0

        elif args.command == "sync-down":
            success = client.sync_library_to_local(
                args.remote_path,
                args.local_folder,
                args.document_library_id,
            )
            print("Sync-down completed successfully" if success else "Sync-down failed")
            return 0 if success else 1

        elif args.command == "sync-up":
            success = client.sync_local_to_library(
                args.local_folder,
                args.remote_path,
                args.document_library_id,
            )
            print("Sync-up completed successfully" if success else "Sync-up failed")
            return 0 if success else 1

        elif args.command == "upload":
            extensions = tuple(e.strip() for e in args.extensions.split(","))
            success = client.upload_folder_to_library(
                args.local_folder,
                args.document_library_id,
                extensions,
            )
            print("Upload completed successfully" if success else "Upload failed")
            return 0 if success else 1

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys

    # If command-line args provided (beyond script name), run CLI
    if len(sys.argv) > 1:
        sys.exit(_main())

    # Otherwise run the original test code
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

    print("\n=== List document libraries ===")
    client.list_document_libraries()

    print("\n=== List root items (default document library) ===")
    client.list_root_items()