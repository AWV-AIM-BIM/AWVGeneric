import logging

from pathlib import Path

from API.auth.enums import AuthType, Environment
from API.clients.locatieservices2_domain import WegsegmentPuntLocatie
from API.auth.factory import RequesterFactory


class Locatieservices2Client:
    def __init__(
        self,
        auth_type: AuthType = None,
        env: Environment = None,
        settings_path: Path | None = None,
        cookie: str | None = None,
        authenticator=None,
        **kwargs,
    ):
        if authenticator is not None:
            self.requester = authenticator.create_requester()
        else:
            if auth_type is None:
                auth_type = kwargs.get("auth")
            if env is None:
                env = kwargs.get("environment")
            self.requester = RequesterFactory.create_requester(
                auth_type=auth_type, env=env, settings_path=settings_path, cookie=cookie, **kwargs
            )
        self.requester.first_part_url += "locatieservices2/"

    def zoek_puntlocatie_via_xy(self, x: float, y: float, zoekafstand: int = 50) -> WegsegmentPuntLocatie:
        response = self.requester.get(url=f"rest/puntlocatie/via/xy?/zoekafstand={zoekafstand}&x={x}&y={y}")
        if response.status_code != 200:
            logging.error(response)
            raise ProcessLookupError(response.content.decode("utf-8"))

        return WegsegmentPuntLocatie.from_dict(response.json())

    def zoek_puntlocatie_via_wegsegment(
        self, ident8: str, opschrift: float, afstand: float = 0.0
    ) -> WegsegmentPuntLocatie:
        response = self.requester.get(
            url=f"rest/puntlocatie/op/weg/{ident8}/via/opschrift?opschrift={opschrift}&afstand={afstand}"
        )
        if response.status_code != 200:
            logging.error(response)
            raise ProcessLookupError(response.content.decode("utf-8"))

        return WegsegmentPuntLocatie.from_dict(response.json())
