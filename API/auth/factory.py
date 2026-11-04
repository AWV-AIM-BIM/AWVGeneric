from pathlib import Path

from API.auth.abstract_requester import AbstractRequester
from API.auth.enums import Environment, AuthType


class RequesterFactory:
    first_part_url_dict = {
        Environment.PRD: "https://services.apps.mow.vlaanderen.be/",
        Environment.TEI: "https://services.apps-tei.mow.vlaanderen.be/",
        Environment.DEV: "https://services.apps-dev.mow.vlaanderen.be/",
        Environment.AIM: "https://services-aim.apps-dev.mow.vlaanderen.be/",
    }

    @classmethod
    def _get_first_part_url(cls, env: Environment) -> str:
        first_part_url = cls.first_part_url_dict.get(env)
        if first_part_url is None:
            raise ValueError(f"Invalid environment: {env}")
        return first_part_url

    @classmethod
    def _resolve_cookie(cls, authenticator, cookie: str | None, settings_filename: str) -> str | None:
        if cookie is not None:
            return cookie
        if authenticator is not None and getattr(authenticator, "cookie", None) is not None:
            return authenticator.cookie
        from API.auth.settings import load_settings

        try:
            settings = load_settings(settings_filename)
            return (
                settings.get("authentication", {})
                .get("COOKIE", {})
                .get((getattr(authenticator, "env", None) or None and authenticator.env.name.lower()) or "", {})
                .get("cookie")
            )
        except Exception:
            return None

    @classmethod
    def _create_cookie_requester(cls, cookie_value: str, first_part_url: str):
        from API.auth.cookie import CookieRequester

        return CookieRequester(cookie=cookie_value, first_part_url=first_part_url.replace("services.", ""))

    @classmethod
    def _create_token_requester(cls, auth_type: AuthType, env: Environment, first_part_url: str, settings_filename: str):
        from API.auth.settings import load_settings

        settings = load_settings(settings_filename)
        specific_settings = settings["authentication"][auth_type.name][env.name.lower()]

        if auth_type == AuthType.JWT:
            from API.auth.jwt import JWTRequester

            return JWTRequester(
                private_key_path=specific_settings["key_path"],
                client_id=specific_settings["client_id"],
                first_part_url=first_part_url,
            )
        if auth_type == AuthType.CERT:
            from API.auth.cert import CertRequester

            return CertRequester(
                cert_path=specific_settings["cert_path"],
                key_path=specific_settings["key_path"],
                first_part_url=first_part_url,
            )
        raise ValueError(f"Invalid authentication type {auth_type}")

    @classmethod
    def create_requester(
        cls,
        auth_type: AuthType = None,
        env: Environment = None,
        settings_path: Path | None = None,
        settings_filename: str | None = None,
        cookie: str | None = None,
        authenticator=None,
        **kwargs,
    ) -> AbstractRequester:
        if authenticator is not None:
            auth_type = authenticator.auth_type
            env = authenticator.env
            cookie = authenticator.cookie
            settings_filename = getattr(authenticator, "settings_filename", settings_filename)

        settings_filename = settings_filename or "settings_AWV_applications.json"
        first_part_url = cls._get_first_part_url(env)

        if auth_type == AuthType.COOKIE:
            cookie_value = cls._resolve_cookie(authenticator, cookie, settings_filename)
            if cookie_value is None:
                raise ValueError("cookie is required for COOKIE authentication (pass as parameter or in settings)")
            return cls._create_cookie_requester(cookie_value, first_part_url)

        return cls._create_token_requester(auth_type, env, first_part_url, settings_filename)

