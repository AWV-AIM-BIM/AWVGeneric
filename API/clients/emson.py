from pathlib import Path

from API.clients.eminfra.EMInfraDomain import BaseDataclass
from API.auth.enums import AuthType, Environment
from API.auth.factory import RequesterFactory


class EMSONClient:
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
        self.requester.first_part_url += 'emson/'

    def get_asset_from_non_referencing_assets(self, asset_uuid: str) -> list[BaseDataclass]:
        url = f'api/asset/assetByUUID?asset_uuid={asset_uuid}'
        json_dict = self.requester.get(url).json()
        return [BaseDataclass.from_dict(asset_dict) for asset_dict in json_dict]
