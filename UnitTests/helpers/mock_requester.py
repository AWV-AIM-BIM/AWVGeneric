from unittest.mock import Mock
from typing import Any, Dict, Optional


class MockResponse:
    def __init__(self, status_code: int = 200, json_data: Any = None, content: bytes = b"", text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        if json_data is not None and isinstance(content, bytes) and content == b"":
            import json

            content = json.dumps(json_data).encode("utf-8")
        self.content = content
        self.text = text or (content.decode("utf-8") if isinstance(content, bytes) else "")

    def json(self):
        if self._json_data is not None:
            return self._json_data
        import json

        return json.loads(self.content.decode("utf-8"))


class MockRequester:
    def __init__(self, responses: Dict[str, MockResponse] | None = None):
        self.responses = responses or {}
        self.calls = []
        self.first_part_url = ""

    def _match(self, method: str, url: str):
        key = f"{method}:{url}"
        if key in self.responses:
            return self.responses[key]
        # try just url
        if url in self.responses:
            return self.responses[url]
        # try suffix match
        for k, v in self.responses.items():
            if k.endswith(url) or url.endswith(k.split(":", 1)[-1]):
                return v
        return None

    def get(self, url: str = "", **kwargs):
        self.calls.append(("GET", url, kwargs))
        resp = self._match("GET", url)
        if resp is None:
            return MockResponse(status_code=200, json_data={})
        return resp

    def post(self, url: str = "", **kwargs):
        self.calls.append(("POST", url, kwargs))
        resp = self._match("POST", url)
        if resp is None:
            # try to be smart - if json/data contains search, return empty search result
            data = kwargs.get("json") or kwargs.get("data")
            if isinstance(data, str) and "search" in url:
                return MockResponse(status_code=200, json_data={"data": [], "totalCount": 0, "from": 0})
            return MockResponse(status_code=200, json_data={})
        return resp

    def put(self, url: str = "", **kwargs):
        self.calls.append(("PUT", url, kwargs))
        resp = self._match("PUT", url)
        if resp is None:
            return MockResponse(status_code=202, json_data={})
        return resp

    def patch(self, url: str = "", **kwargs):
        self.calls.append(("PATCH", url, kwargs))
        resp = self._match("PATCH", url)
        if resp is None:
            return MockResponse(status_code=202, json_data={})
        return resp

    def delete(self, url: str = "", **kwargs):
        self.calls.append(("DELETE", url, kwargs))
        resp = self._match("DELETE", url)
        if resp is None:
            return MockResponse(status_code=202, json_data={})
        return resp
