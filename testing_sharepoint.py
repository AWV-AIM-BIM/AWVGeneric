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

    client.list_document_libraries()  # List all document libraries

# Download entire document library to local mirror
    local_mirror = Path("local_mirror") / "AIMData"
    success = client.sync_library_to_local("", local_mirror, 'b!GOUfzY4L9U--LXscHHb0hfzWhuzY3f5IsZck59FWs06h6NB4Vk2bSKIGr6651wus')
    if success:
        print(f"✅ Download completed to {local_mirror}")
    else:
        print("❌ Download failed")