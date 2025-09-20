from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from .status import CLOSED_STATUSES


@dataclass
class IssueBase:
    key: str
    project: str
    type: str
    title: str
    status: str
    labels: List[str] = field(default_factory=list)
    prio: Optional[str] = None

    def __str__(self) -> str:
        return " | ".join([self.key, self.type, self.status, self.title])


@dataclass
class LVL2Epic(IssueBase):
    blfnt: str = "na"


@dataclass
class LVL2Feature(IssueBase):
    pu: str = "na"


@dataclass
class PCIssue(IssueBase):
    components: List[str] = field(default_factory=list)
    story_points: int = 0

    def is_closed(self) -> bool:
        return self.status in CLOSED_STATUSES

    def is_network(self) -> bool:
        return "Network" in self.components


@dataclass
class PCIEpic(PCIssue):
    pass


@dataclass
class PCITaskStory(PCIssue):
    pass
