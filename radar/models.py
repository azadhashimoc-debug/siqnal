from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


@dataclass
class Record:
    source: str
    kind: Literal["news", "comment"]
    url: str
    text: str
    published: datetime
    parent_url: Optional[str] = None
