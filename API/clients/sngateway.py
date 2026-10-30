from pathlib import Path

from API.Enums import AuthType, Environment
from API.RequesterFactory import RequesterFactory


class SNGatewayClient:
    def __init__(self, auth_type: AuthType = None, env: Environment = None, settings_path: Path = None,
                 cookie: str = None, authenticator=None, **kwargs):
        if authenticator is not None:
            self.requester = authenticator.create_requester()
        else:
            if auth_type is None:
                auth_type = kwargs.get('auth')
            if env is None:
                env = kwargs.get('environment')
            self.requester = RequesterFactory.create_requester(auth_type=auth_type, env=env,
                                                               settings_path=settings_path,
                                                               cookie=cookie, **kwargs)
        self.requester.first_part_url += 'services/'

    def get_assets(self):
        url = 'asset-service/rest/assets?SysparmLimit=1&SysparmOffset=0'
        return self.requester.get(url).json()

    def get_asset_by_guid(self, guid):
        url = f'asset-service/rest/assets/{guid}'
        response = self.requester.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError(response.content.decode("utf-8"))

    def get_assets_by_id_list(self, id_list: list):
        url = 'asset-service/rest/assets'
        request_body = {
            "assetIds": id_list
        }
        return self.requester.post(url, json=request_body).json()

    def update_asset(self, guid: str, put_body: dict):
        url = f'asset-service/rest/assets/{guid}'
        return self.requester.put(url, json=put_body).json()

    def get_asset_logs_by_guid(self, guid: str):
        url = f'asset-service/rest/assets/{guid}/logs'
        return self.requester.get(url).json()

    def search_assets(self, query: str = None, sysparm_query: str = None, limit: int = 100,
                       offset: int = 0):
        if sysparm_query is not None:
            url = f'asset-service/rest/assets?sysparm_query={sysparm_query}&sysparm_limit={limit}&sysparm_offset={offset}'
        elif query is not None:
            url = f'asset-service/rest/assets?sysparm_query={query}&sysparm_limit={limit}&sysparm_offset={offset}'
        else:
            url = f'asset-service/rest/assets?sysparm_limit={limit}&sysparm_offset={offset}'
        return self.requester.get(url).json()

    def get_table(self, table_name: str, sysparm_query: str = None, limit: int = 100, offset: int = 0):
        if sysparm_query:
            url = f'{table_name}?sysparm_query={sysparm_query}&sysparm_limit={limit}&sysparm_offset={offset}'
        else:
            url = f'{table_name}?sysparm_limit={limit}&sysparm_offset={offset}'
        return self.requester.get(url).json()
