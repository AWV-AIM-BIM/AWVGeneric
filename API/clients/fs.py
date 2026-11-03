from pathlib import Path

from API.auth.enums import AuthType, Environment
from API.auth.factory import RequesterFactory


class FSClient:
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
        self.requester.first_part_url += 'fileservice/'

    def get_file(self, file_id: str):
        url = f'fileservice?fileId={file_id}'
        return self.requester.get(url).content

    def get_by_uuid(self, uuid: str):
        url = f'api/file/{uuid}'
        response = self.requester.get(url)
        return response.content
