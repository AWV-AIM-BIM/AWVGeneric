import json
from pathlib import Path

from API.SharepointClient import SharepointClient

config_path = Path(__file__).parent.parent / "config" / "settings_Sharepoint.json"
with open(config_path) as f:
    config = json.load(f)

if __name__ == '__main__':
    client = SharepointClient(
        client_id=config["client_id"],
        tenant_id=config["tenant_id"],
        client_secret=config["secret"],
        site_url=config["site_url"],
    )

    client.list_drives()  # List all drives
    client.list_root_files()  # List files in all drives
    client.list_drive_files('b!GOUfzY4L9U--LXscHHb0hfzWhuzY3f5IsZck59FWs06h6NB4Vk2bSKIGr6651wus')  # List files in a specific drive