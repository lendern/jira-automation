from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from .status import CLOSED_STATUSES
from .fields import FieldAccessMixin


@dataclass
class IssueBase(FieldAccessMixin):
    key: str
    project: str
    type: str
    title: str
    status: str
    labels: List[str] = field(default_factory=list)
    prio: Optional[str] = None

    def __str__(self) -> str:
        return " | ".join([self.key, self.type, self.status, self.title])

    def __hash__(self) -> int:
        # Hash by stable identity (issue key) so domain objects are usable
        # with libraries that require hashing (e.g., tree nodes de-dup).
        return hash(self.key)


@dataclass
class LVL2Epic(IssueBase):
    blfnt: str = "na"

    def __hash__(self) -> int:
        return hash(self.key)


@dataclass
class LVL2Feature(IssueBase):
    pu: str = "na"

    def __hash__(self) -> int:
        return hash(self.key)


@dataclass
class PCIssue(IssueBase):
    components: List[str] = field(default_factory=list)
    story_points: int = 0

    def is_closed(self) -> bool:
        return self.status in CLOSED_STATUSES

    def is_network(self) -> bool:
        return "Network" in self.components

    def __hash__(self) -> int:
        return hash(self.key)


@dataclass
class PCIEpic(PCIssue):
    def __hash__(self) -> int:
        return hash(self.key)


@dataclass
class PCITaskStory(PCIssue):
    def __hash__(self) -> int:
        return hash(self.key)
