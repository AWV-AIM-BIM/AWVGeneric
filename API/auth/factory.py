from pathlib import Path

from API.AbstractRequester import AbstractRequester
from API.Enums import Environment, AuthType


class RequesterFactory:
    first_part_url_dict = {
        Environment.PRD: 'https://services.apps.mow.vlaanderen.be/',
        Environment.TEI: 'https://services.apps-tei.mow.vlaanderen.be/',
        Environment.DEV: 'https://services.apps-dev.mow.vlaanderen.be/',
        Environment.AIM: 'https://services-aim.apps-dev.mow.vlaanderen.be/'
    }

    @classmethod
    def create_requester(
        cls,
        auth_type: AuthType = None,
        env: Environment = None,
        settings_path: Path = None,
        settings_filename: str = None,
        cookie: str = None,
        authenticator=None,
        **kwargs
    ) -> AbstractRequester:
        if authenticator is not None:
            auth_type = authenticator.auth_type
            env = authenticator.env
            cookie = authenticator.cookie
            settings_filename = getattr(authenticator, 'settings_filename', settings_filename)
        
        settings_filename = settings_filename or "settings_AWV_applications.json"
        
        first_part_url = cls.first_part_url_dict.get(env)
        if first_part_url is None:
            raise ValueError(f"Invalid environment: {env}")

        if auth_type == AuthType.COOKIE:
            cookie_value = cookie
            if cookie_value is None:
                from API.settings_finder import load_settings
                try:
                    settings = load_settings(settings_filename)
                    cookie_value = settings.get('authentication', {}).get('COOKIE', {}).get(env.name.lower(), {}).get('cookie')
                except Exception:
                    pass
            if cookie_value is None:
                raise ValueError("cookie is required for COOKIE authentication (pass as parameter or in settings)")
            from API.CookieRequester import CookieRequester
            return CookieRequester(cookie=cookie_value, first_part_url=first_part_url.replace('services.', ''))

        from API.settings_finder import load_settings
        settings = load_settings(settings_filename)
        specific_settings = settings['authentication'][auth_type.name][env.name.lower()]

        if auth_type == AuthType.JWT:
            from API.JWTRequester import JWTRequester
            return JWTRequester(private_key_path=specific_settings['key_path'],
                                client_id=specific_settings['client_id'],
                                first_part_url=first_part_url)
        elif auth_type == AuthType.CERT:
            from API.CertRequester import CertRequester
            return CertRequester(cert_path=specific_settings['cert_path'],
                                 key_path=specific_settings['key_path'],
                                 first_part_url=first_part_url)
        else:
            raise ValueError(f"Invalid authentication type {auth_type}")
