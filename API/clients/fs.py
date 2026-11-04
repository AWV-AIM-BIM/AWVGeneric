from pathlib import Path

from tqdm import tqdm

from API.auth.enums import AuthType, Environment
from API.auth.factory import RequesterFactory


class FSClient:
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
        self.requester.first_part_url += "geolatte-nosqlfs/cert/api/databases/featureserver/"

    def download_layer(self, layer: str, file_path: Path) -> None:
        response = self.requester.get(url=f"{layer}/query?fmt=json&projection=properties", stream=True)
        if response.status_code != 200:
            raise ProcessLookupError(response.content.decode("utf-8"))

        total_size = 0
        chunk_size = 1024 * 1024

        with open(file_path, "wb") as f, tqdm(unit_scale=True, unit="B", desc=file_path.name) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
                    pbar.update(len(chunk))


    def download_layer_to_records(self, layer: str, chunk_size: int = 1024 * 256):
        response = self.requester.get(url=f"{layer}/query?fmt=json&projection=properties", stream=True)
        if response.status_code != 200:
            raise ProcessLookupError(response.content.decode("utf-8"))

        chunk_rest = ""

        with tqdm(unit=" records", desc=layer) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    chunk_rest += chunk.decode("utf-8")
                    chunk_rest = yield from self._process_chunk(chunk_rest, pbar)
                elif chunk_rest:
                    chunk_rest = yield from self._process_chunk(chunk_rest, pbar)


    @classmethod
    def _process_chunk(cls, chunk_rest, pbar) -> str:
        chunks = chunk_rest.split("\n")
        chunk_rest = chunks.pop(-1)
        pbar.update(len(chunks))
        yield from chunks
        return chunk_rest
