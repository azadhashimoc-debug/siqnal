from typing import Iterable, Protocol

from radar.models import Record


class Source(Protocol):
    name: str

    def fetch(self) -> Iterable[Record]: ...
