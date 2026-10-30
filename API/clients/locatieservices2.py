from pathlib import Path

from API.Enums import AuthType, Environment
from API.Locatieservices2Domain import WegsegmentPuntLocatie
from API.RequesterFactory import RequesterFactory


class Locatieservices2Client:
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
        self.requester.first_part_url += 'locatieservices2/'

    def get_by_wkt(self, wkt_string: str, distance: int = 50, limit: int = 1000) -> [WegsegmentPuntLocatie]:
        url = f'v1/locaties/wkt?WKT={wkt_string}&distance={distance}&limit={limit}'
        json_dict = self.requester.get(url).json()
        return [WegsegmentPuntLocatie.from_dict(wegsegment_dict) for wegsegment_dict in json_dict['features']]
