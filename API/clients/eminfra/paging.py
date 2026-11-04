from collections.abc import Generator
from typing import Optional, TypeVar

from API.clients.eminfra.EMInfraDomain import BaseDataclass

T = TypeVar("T", bound=BaseDataclass)


def offset_page_generator_get(
    requester,
    base: str,
    resource: str,
    page_size: int,
    start_from: Optional[int] = None,
    dto_type: Optional[type[T]] = None,
    include_paging_mode: bool = True,
) -> Generator[tuple[Optional[int], list], None, None]:
    """Generic offset paging generator for AWV GET endpoints.

    Yields ``(next_start_or_None, data_list)`` per page until exhausted.
    ``data_list`` contains raw dicts unless ``dto_type`` is provided, in which
    case each item is converted via ``dto_type.from_dict``.

    Args:
        requester: An AbstractRequester-like object with a ``get`` method.
        base: API base path segment, e.g. ``"core"`` or ``"identiteit"``.
        resource: Resource collection name, e.g. ``"assettypes"``.
        page_size: Number of items per page.
        start_from: Optional offset to start from (defaults to 0).
        dto_type: Optional dataclass subclass with a ``from_dict`` classmethod.
        include_paging_mode: Whether to append ``pagingMode=OFFSET`` to the URL.
    """
    _from = start_from if start_from is not None else 0
    while True:
        if include_paging_mode:
            url = f"{base}/api/{resource}?from={_from}&pagingMode=OFFSET&size={page_size}"
        else:
            url = f"{base}/api/{resource}?from={_from}&size={page_size}"
        json_dict = requester.get(url).json()
        raw_list = json_dict.get("data", [])
        if dto_type is not None:
            data_list: list[T] = [dto_type.from_dict(item) for item in raw_list]
        else:
            data_list = raw_list
        total_count = json_dict.get("totalCount", 0)
        server_from = json_dict.get("from", _from)
        next_start = server_from + page_size
        if next_start >= total_count:
            next_start = None
        yield (next_start, data_list)
        if next_start is None:
            break
        _from = next_start
