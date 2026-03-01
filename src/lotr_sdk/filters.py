"""Filter helpers for The One API query syntax."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote


@dataclass(frozen=True)
class FilterExpr:
    """Represents one API filter expression for a field."""

    field: str
    operator: str
    value: Any

    def to_fragment(self) -> str:
        if self.operator == "exists":
            return self.field
        encoded_value = quote(str(self.value), safe="/,")
        return f"{self.field}{self.operator}{encoded_value}"


class F:
    """Fluent filter constructors.

    Example:
        F.runtime.gt(100), F.name.regex("Ring")
    """

    def __init__(self, field: str) -> None:
        self.field = field

    def eq(self, value: Any) -> FilterExpr:
        return FilterExpr(self.field, "=", value)

    def ne(self, value: Any) -> FilterExpr:
        return FilterExpr(self.field, "!=", value)

    def include(self, values: list[Any]) -> FilterExpr:
        return FilterExpr(self.field, "=", ",".join(map(str, values)))

    def exclude(self, values: list[Any]) -> FilterExpr:
        return FilterExpr(self.field, "!=", ",".join(map(str, values)))

    def lt(self, value: Any) -> FilterExpr:
        return FilterExpr(self.field, "<", value)

    def lte(self, value: Any) -> FilterExpr:
        return FilterExpr(self.field, "<=", value)

    def gt(self, value: Any) -> FilterExpr:
        return FilterExpr(self.field, ">", value)

    def gte(self, value: Any) -> FilterExpr:
        return FilterExpr(self.field, ">=", value)

    def regex(self, value: str) -> FilterExpr:
        return FilterExpr(self.field, "=", f"/{value}/")

    def exists(self) -> FilterExpr:
        return FilterExpr(self.field, "exists", "")


class Fields:
    """Factory for dynamic field helpers: fields.name.gt(1)."""

    def __getattr__(self, name: str) -> F:
        return F(name)


fields = Fields()
