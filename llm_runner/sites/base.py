from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SiteResult:
    response_text: str


class SiteAdapter(Protocol):
    name: str

    def open(self) -> None: ...
    def submit_and_get_response(self, query: str) -> SiteResult: ...

