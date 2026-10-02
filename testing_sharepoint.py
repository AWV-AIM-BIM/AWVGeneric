import os

from API.SharepointClient import SharepointClient

if __name__ == '__main__':
    client = SharepointClient(
        client_id=os.getenv("CLIENT_ID"),
        tenant_id=os.getenv("TENANT_ID"),
        client_secret=os.getenv("SECRET"),
        site_url="https://vlaamseoverheid.sharepoint.com/sites/AIW_AIM_BIM/AIMData",
    )

    client.list_drives()  # List all drives
    client.list_root_files()  # List files in all drives
    client.list_drive_files('b!GOUfzY4L9U--LXscHHb0hfzWhuzY3f5IsZck59FWs06h6NB4Vk2bSKIGr6651wus')  # List files in a specific drive