from __future__ import annotations

import ipaddress
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


class AppSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_network_values(cls, value):
        if isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            return str(value)
        return value


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
