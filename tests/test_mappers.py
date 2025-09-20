from lsd.mappers import to_domain
from lsd.models import LVL2Epic, LVL2Feature, PCIEpic, PCITaskStory, IssueBase


class DummyIssue:
    def __init__(self, key: str, fields):
        self.key = key
        self.fields = fields


class Attr:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_map_lvl2_epic():
    fields = Attr(
        project=Attr(key="LVL2"),
        issuetype=Attr(name="Epic LPM"),
        summary="An LVL2 epic",
        status=Attr(name="In Progress"),
        priority=Attr(name="High"),
        labels=["l1", "l2"],
        customfield_10530=Attr(value="blfntX"),
    )
    d = to_domain(DummyIssue("LVL2-1", fields))
    assert isinstance(d, LVL2Epic)
    assert d.key == "LVL2-1"
    assert d.type == "Epic LPM"
    assert d.status == "In Progress"
    assert d.prio == "High"
    assert d.labels == ["l1", "l2"]
    assert d.blfnt == "blfntX"


def test_map_lvl2_feature():
    fields = Attr(
        project=Attr(key="LVL2"),
        issuetype=Attr(name="New Feature"),
        summary="A feature",
        status=Attr(name="Open"),
        priority=Attr(name="Medium"),
        labels=[],
        customfield_16708=Attr(value="puY"),
    )
    d = to_domain(DummyIssue("LVL2-2", fields))
    assert isinstance(d, LVL2Feature)
    assert d.pu == "puY"


def test_map_pci_epic_components_and_points():
    fields = Attr(
        project=Attr(key="PCI"),
        issuetype=Attr(name="Epic"),
        summary="PCI epic",
        status=Attr(name="To Do"),
        priority=Attr(name="Highest"),
        labels=["L"],
        components=[Attr(name="Network"), Attr(name="Compute")],
        customfield_10006="13",
    )
    d = to_domain(DummyIssue("PCI-10", fields))
    assert isinstance(d, PCIEpic)
    assert sorted(d.components) == ["Compute", "Network"]
    assert d.story_points == 13


def test_map_pci_story_default_points():
    fields = Attr(
        project=Attr(key="PCI"),
        issuetype=Attr(name="Story"),
        summary="A story",
        status=Attr(name="To Do"),
        priority=Attr(name="Low"),
        labels=[],
        components=[Attr(name="Network")],
        customfield_10006=None,
    )
    d = to_domain(DummyIssue("PCI-11", fields))
    assert isinstance(d, PCITaskStory)
    assert d.story_points == 0


def test_map_unknown_fallback_issuebase():
    fields = Attr(
        project=Attr(key="ABC"),
        issuetype=Attr(name="Bug"),
        summary="Something else",
        status=Attr(name="Open"),
        priority=Attr(name="P2"),
        labels=["x"],
    )
    d = to_domain(DummyIssue("ABC-1", fields))
    assert isinstance(d, IssueBase)
    assert d.project == "ABC"
    assert d.type == "Bug"
