from lsd.mappers import to_domain
from lsd.models import IssueBase, PCIssue


def test_to_domain_unknown_maps_to_issuebase():
    """Le test vérifie qu'un ticket non supporté est mappé vers IssueBase avec les attributs de base."""
    from tests.conftest import FakeIssue

    raw = {
        "project": {"key": "XYZ"},
        "issuetype": {"name": "Weird"},
        "summary": "mystery",
        "status": {"name": "Unknown"},
        "priority": {"name": "High"},
        "labels": ["L1"],
    }
    issue = FakeIssue("XYZ-1", raw)
    dom = to_domain(issue)
    assert isinstance(dom, IssueBase)
    assert not isinstance(dom, PCIssue)
    assert dom.key == "XYZ-1"
    assert dom.project == "XYZ"
    assert dom.type == "Weird"
    assert dom.title == "mystery"
    assert dom.status == "Unknown"
    assert dom.prio == "High"
    assert dom.labels == ["L1"]
