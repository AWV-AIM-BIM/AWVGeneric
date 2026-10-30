from pathlib import Path
from typing import Optional, Union

from API.clients.eminfra.AgentService import AgentService
from API.clients.eminfra.AssetService import AssetService
from API.clients.eminfra.AssettypeService import AssettypeService
from API.clients.eminfra.BeheerobjectService import BeheerobjectService
from API.clients.eminfra.BestekService import BestekService
from API.clients.eminfra.DocumentService import DocumentService
from API.clients.eminfra.EigenschapService import EigenschapService
from API.clients.eminfra.EventService import EventService
from API.clients.eminfra.FeedService import FeedService
from API.clients.eminfra.GeometrieService import GeometrieService
from API.clients.eminfra.GraphService import GraphService
from API.clients.eminfra.KenmerkService import KenmerkService
from API.clients.eminfra.LocatieService import LocatieService
from API.clients.eminfra.OnderdeelService import OnderdeelService
from API.clients.eminfra.PostitService import PostitService
from API.clients.eminfra.RelatieService import RelatieService
from API.clients.eminfra.SchadebeheerderService import SchadebeheerderService
from API.clients.eminfra.ToezichterService import ToezichterService

from API.auth.enums import AuthType, Environment
from API.auth.factory import RequesterFactory


class EMInfraClient:
    def __init__(
        self,
        auth_type: AuthType = None,
        env: Environment = None,
        settings_path: Path = None,
        cookie: str = None,
        authenticator=None,
        **kwargs
    ):
        if authenticator is not None:
            self.requester = authenticator.create_requester()
        else:
            # Allow passing via kwargs for flexibility
            if auth_type is None:
                auth_type = kwargs.get('auth')
            if env is None:
                env = kwargs.get('environment')
            self.requester = RequesterFactory.create_requester(
                auth_type=auth_type,
                env=env,
                settings_path=settings_path,
                cookie=cookie,
                **kwargs
            )
        self.requester.first_part_url += 'eminfra/'

        # Sub-services
        self.agent_service = AgentService(self.requester)
        self.asset_service = AssetService(self.requester)
        self.assettype_service = AssettypeService(self.requester)
        self.beheerobject_service = BeheerobjectService(self.requester)
        self.bestek_service = BestekService(self.requester)
        self.document_service = DocumentService(self.requester)
        self.eigenschap_service = EigenschapService(self.requester)
        self.event_service = EventService(self.requester)
        self.feed_service = FeedService(self.requester)
        self.geometrie_service = GeometrieService(self.requester)
        self.graph_service = GraphService(self.requester)
        self.kenmerk_service = KenmerkService(self.requester)
        self.locatie_service = LocatieService(self.requester)
        self.onderdeel_service = OnderdeelService(self.requester)
        self.postit_service = PostitService(self.requester)
        self.relatie_service = RelatieService(self.requester)
        self.schadebeheerder_service = SchadebeheerderService(self.requester)
        self.toezichter_service = ToezichterService(self.requester)

    def get_oef_schema_as_json(self, name: str) -> str:
        url = f"core/api/otl/schema/oef/{name}"
        content = self.requester.get(url).content
        return content.decode("utf-8")