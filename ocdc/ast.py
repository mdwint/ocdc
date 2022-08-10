from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class ChangeType(Enum):
    Added = "Added"
    Changed = "Changed"
    Deprecated = "Deprecated"
    Removed = "Removed"
    Fixed = "Fixed"
    Security = "Security"


class ListItem(BaseModel):
    text: str
    level: int = 0


class Changes(BaseModel):
    items: List[ListItem]
    footer: str = ""

    def merge(self, other: "Changes") -> None:
        self.items.extend(other.items)
        self.footer = f"{self.footer}\n{other.footer}".strip()


class Version(BaseModel):
    number: str
    date: str = ""
    changes: Dict[str, Changes] = Field(default_factory=dict)


class Changelog(BaseModel):
    title: str = ""
    intro: str = ""
    versions: List[Version] = Field(default_factory=list)
