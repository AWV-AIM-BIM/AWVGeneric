from pathlib import Path

from API.auth.enums import AuthType, Environment
from API.auth.factory import RequesterFactory


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
        self.requester.first_part_url += 'sngateway/'

    def get_all_asset_filters(self) -> list[dict]:
        url = 'rest/eminfra/asset-filter'
        response = self.requester.get(url=url)
        return response.json()

    def add_new_asset_filter(self, uri: str, enabled: bool = True) -> None:
        url = 'rest/eminfra/asset-filter'
        response = self.requester.post(url=url, json={
          "uri": uri,
          "enabled": enabled
        })
        return response.json()

    def modify_asset_filter(self, id: str, uri: str, enabled: bool = True) -> None:
        url = f'rest/eminfra/asset-filter/{id}'
        response = self.requester.put(url=url, json={
          "uri": uri,
          "enabled": enabled
        })
        return response.json()

    def enable_asset_filter(self, uri: str) -> None:
        existing_filters = self.get_all_asset_filters()
        existing_filter = next((filter for filter in existing_filters if filter['uri'] == uri), None)
        if existing_filter is None:
            self.add_new_asset_filter(uri=uri, enabled=True)
        else:
            if existing_filter['enabled']:
                print(f'Filter with uri {uri} is already enabled')
                return
            self.modify_asset_filter(id=existing_filter['id'], uri=uri, enabled=True)

    def disable_asset_filter(self, uri: str) -> None:
        existing_filters = self.get_all_asset_filters()
        existing_filter = next((filter for filter in existing_filters if filter['uri'] == uri), None)
        if existing_filter is None:
            self.add_new_asset_filter(uri=uri, enabled=False)
        else:
            if not existing_filter['enabled']:
                print(f'Filter with uri {uri} is already disabled')
                return
            self.modify_asset_filter(id=existing_filter['id'], uri=uri, enabled=False)
