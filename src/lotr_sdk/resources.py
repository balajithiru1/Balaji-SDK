"""Resource classes for endpoint groups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union

from .filters import FilterExpr
from .models import APIResponse


def _merge_params(
    *,
    limit: Optional[int] = None,
    page: Optional[int] = None,
    offset: Optional[int] = None,
    sort: Optional[str] = None,
    filters: Optional[Union[Iterable[FilterExpr], Dict[str, Any]]] = None,
) -> Tuple[Dict[str, str], List[str]]:
    params: Dict[str, str] = {}
    filter_fragments: List[str] = []

    if limit is not None:
        params["limit"] = str(limit)
    if page is not None:
        params["page"] = str(page)
    if offset is not None:
        params["offset"] = str(offset)
    if sort is not None:
        params["sort"] = sort

    if filters is None:
        return params, filter_fragments

    if isinstance(filters, dict):
        for key, value in filters.items():
            key_str = str(key)
            if key_str in {"sort", "limit", "page", "offset"}:
                params[key_str] = str(value)
                continue
            if any(op in key_str for op in ("!=", ">=", "<=", "=", ">", "<")):
                filter_fragments.append(f"{key_str}{value}")
            else:
                filter_fragments.append(f"{key_str}={value}")
        return params, filter_fragments

    for expr in filters:
        filter_fragments.append(expr.to_fragment())

    return params, filter_fragments


class BaseResource:
    def __init__(self, client: "LOTRClient") -> None:
        self._client = client

    def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
        filter_fragments: Optional[List[str]] = None,
    ) -> APIResponse:
        return self._client.get(path, params=params, filter_fragments=filter_fragments)


class MovieResource(BaseResource):
    def list(
        self,
        *,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[str] = None,
        filters: Optional[Union[Iterable[FilterExpr], Dict[str, Any]]] = None,
    ) -> APIResponse:
        params, filter_fragments = _merge_params(
            limit=limit, page=page, offset=offset, sort=sort, filters=filters
        )
        return self._get("/movie", params=params, filter_fragments=filter_fragments)

    def get(self, movie_id: str) -> APIResponse:
        return self._get(f"/movie/{movie_id}")

    def quotes(
        self,
        movie_id: str,
        *,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[str] = None,
        filters: Optional[Union[Iterable[FilterExpr], Dict[str, Any]]] = None,
    ) -> APIResponse:
        params, filter_fragments = _merge_params(
            limit=limit, page=page, offset=offset, sort=sort, filters=filters
        )
        return self._get(
            f"/movie/{movie_id}/quote", params=params, filter_fragments=filter_fragments
        )


class QuoteResource(BaseResource):
    def list(
        self,
        *,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[str] = None,
        filters: Optional[Union[Iterable[FilterExpr], Dict[str, Any]]] = None,
    ) -> APIResponse:
        params, filter_fragments = _merge_params(
            limit=limit, page=page, offset=offset, sort=sort, filters=filters
        )
        return self._get("/quote", params=params, filter_fragments=filter_fragments)

    def get(self, quote_id: str) -> APIResponse:
        return self._get(f"/quote/{quote_id}")


if TYPE_CHECKING:
    from .client import LOTRClient
