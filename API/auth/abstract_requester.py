import abc
from typing import Any, Callable, Optional

from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry


class AbstractRequester(Session, metaclass=abc.ABCMeta):
    """A `requests.Session` with a base URL prefix and simple retry behavior.

    This class is meant to be subclassed by concrete requesters that configure
    authentication, headers, certificates, etc. All HTTP verb methods here are
    functional (not abstract) and will:

    - prepend `first_part_url` to the provided `url`
    - retry up to `retries` times
    - return the first 2xx response
    - raise `RuntimeError` after retries are exhausted

    Notes:
        - Uses urllib3 Retry for robust retry logic with backoff.
        - Retries on connection errors, read errors, and specific status codes.
        - Has sensible default timeouts.
    """

    def __init__(
        self,
        first_part_url: str = "",
        retries: int = 3,
        retry_status_codes: tuple = (429, 500, 502, 503, 504),
        backoff_factor: float = 0.5,
        timeout: tuple = (3.05, 30),
    ):
        """Create a requester.

        Args:
            first_part_url: Prefix added to every request URL.
            retries: Number of attempts for each request (must be >= 1).
            retry_status_codes: HTTP status codes to retry on.
            backoff_factor: Backoff factor for exponential delay.
            timeout: Default timeout (connect, read) in seconds.
        """
        super().__init__()
        self.first_part_url = first_part_url
        self.default_timeout = timeout

        if retries < 1:
            raise ValueError("retries must be at least 1")
        self.retries = retries
        self.retry_status_codes = retry_status_codes
        self.backoff_factor = backoff_factor

        # Configure urllib3 Retry with exponential backoff
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=backoff_factor,
            status_forcelist=retry_status_codes,
            allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    def get(self, url: str = "", **kwargs: Any) -> Response:
        """Send a GET request with base URL + retries."""
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.default_timeout
        return self._request_with_retries(super().get, "GET", url, **kwargs)

    def post(self, url: str = "", **kwargs: Any) -> Response:
        """Send a POST request with base URL + retries."""
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.default_timeout
        return self._request_with_retries(super().post, "POST", url, **kwargs)

    def put(self, url: str = "", **kwargs: Any) -> Response:
        """Send a PUT request with base URL + retries."""
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.default_timeout
        return self._request_with_retries(super().put, "PUT", url, **kwargs)

    def patch(self, url: str = "", **kwargs: Any) -> Response:
        """Send a PATCH request with base URL + retries."""
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.default_timeout
        return self._request_with_retries(super().patch, "PATCH", url, **kwargs)

    def delete(self, url: str = "", **kwargs: Any) -> Response:
        """Send a DELETE request with base URL + retries."""
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.default_timeout
        return self._request_with_retries(super().delete, "DELETE", url, **kwargs)

    def _request_with_retries(
        self,
        request_func: Callable[..., Response],
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Response:
        """Execute a request function with retries and consistent error reporting.

        Args:
            request_func: Typically `super().get/post/...`.
            method: HTTP method name (for error messages).
            url: URL path or full URL fragment to append to `first_part_url`.
            **kwargs: Forwarded to `requests`.

        Returns:
            The first successful response (`Response.ok` is True).

        Raises:
            RuntimeError: when all retries are exhausted.
        """
        full_url = f"{self.first_part_url}{url}"
        last_response: Optional[Response] = None
        last_exception: Optional[BaseException] = None

        for _ in range(self.retries):
            try:
                last_response = request_func(url=full_url, **kwargs)
            except RequestException as exc:
                last_exception = exc
                continue

            if last_response.ok:
                return last_response

        error_details = self._get_error_details_from_response(last_response)
        response_summary = str(last_response) if last_response is not None else "<no response>"
        exception_summary = (
            f"\nLast exception: {last_exception}" if last_exception is not None else ""
        )

        raise RuntimeError(
            f"{method} request failed after {self.retries} retries. "
            f"Last response: {response_summary}\n"
            f"Error details: {error_details}"
            f"{exception_summary}"
        )

    def _get_error_details_from_response(self, response: Optional[Response]) -> object:
        """Extract the most useful error details from a response.

        Tries JSON first (and returns the `message` field when present), then
        falls back to decoding the raw content.

        Args:
            response: The most recent response (may be None if all attempts
                failed due to exceptions).

        Returns:
            A best-effort error object (dict/str/bytes/None).
        """
        if response is None:
            return None

        try:
            payload = response.json()
            if isinstance(payload, dict):
                return payload.get("message", payload)
            return payload
        except Exception:
            pass

        try:
            return response.content.decode("utf-8", errors="replace")
        except Exception:
            return response.content
