"""
lsd.models

Domain models for LVL2/LVL3 issues. Models are POPOs (plain objects)
that do not perform network calls. Use `from_jira(issue)` to build them
from jira-python Issue objects.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IssueBase:
    key: str
    project: str
    type: str
    title: str
    status: str
    prio: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    childs: List[str] = field(default_factory=list)

    @classmethod
    def from_jira(cls, issue):
        f = issue.fields
        return cls(
            key=issue.key,
            project=f.project.key,
            type=f.issuetype.name,
            title=f.summary,
            status=f.status.name,
            prio=getattr(f.priority, 'name', None),
            labels=getattr(f, 'labels', []) or [],
            childs=[],
        )


@dataclass
class LVL2Feature(IssueBase):
    pu: Optional[str] = 'na'

    @classmethod
    def from_jira(cls, issue):
        base = IssueBase.from_jira(issue)
        _fields = issue.fields
        pu = getattr(_fields, 'customfield_16708', None)
        if pu:
            pu_val = getattr(pu, 'value', 'na')
        else:
            pu_val = 'na'
        return cls(**base.__dict__, pu=pu_val)


@dataclass
class LVL2Epic(IssueBase):
    blfnt: Optional[str] = 'na'

    @classmethod
    def from_jira(cls, issue):
        base = IssueBase.from_jira(issue)
        _fields = issue.fields
        blf = getattr(_fields, 'customfield_10530', None)
        blf_val = getattr(blf, 'value', 'na') if blf else 'na'
        return cls(**base.__dict__, blfnt=blf_val)


@dataclass
class PCIEpic(IssueBase):
    components: List[str] = field(default_factory=list)

    @classmethod
    def from_jira(cls, issue):
        base = IssueBase.from_jira(issue)
        _fields = issue.fields
        comps = [c.name for c in getattr(_fields, 'components', [])]
        return cls(**base.__dict__, components=comps)


@dataclass
class PCITaskStory(IssueBase):
    estimate: int = 0

    @classmethod
    def from_jira(cls, issue):
        base = IssueBase.from_jira(issue)
        _fields = issue.fields
        est = getattr(_fields, 'customfield_10006', None)
        try:
            est_val = int(est) if est else 0
        except Exception:
            est_val = 0
        return cls(**base.__dict__, estimate=est_val)
