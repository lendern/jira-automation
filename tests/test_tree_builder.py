from lsd.tree_builder import build_lsd_tree
from lsd.mappers import to_domain


class RepoWithSearch:
    def __init__(self, state, edges_parent, edges_epic):
        self.state = state
        self.edges_parent = edges_parent
        self.edges_epic = edges_epic

    # Minimal read API
    def get_issue(self, key: str):
        from tests.conftest import FakeIssue

        return FakeIssue(key, self.state.get(key, {}))

    # Search API used by tree_builder
    def find_lvl2_new_features(self, sprint: str, squad: str):
        return [k for k, v in self.state.items() if v.get("_root")]

    def find_pci_children_by_parent_link(self, parent_key: str):
        return list(self.edges_parent.get(parent_key, []))

    def find_children_by_epic_link(self, epic_key: str, squad: str):
        return list(self.edges_epic.get(epic_key, []))


def _fields_lv12_feature(summary="feat", pu=None):
    return {
        "project": {"key": "LVL2"},
        "issuetype": {"name": "New Feature"},
        "summary": summary,
        "status": {"name": "Open"},
        "priority": {"name": "Medium"},
        "labels": [],
        "customfield_16708": {"value": pu} if pu is not None else None,
    }


def _fields_pci_epic(summary="pci epic", comps=None, sp=None, status="To Do"):
    return {
        "project": {"key": "PCI"},
        "issuetype": {"name": "Epic"},
        "summary": summary,
        "status": {"name": status},
        "priority": {"name": "Medium"},
        "labels": [],
        "components": [{"name": c} for c in (comps or [])],
        "customfield_10006": sp,
    }


def _fields_pci_task(summary="task", comps=None, sp=None, status="To Do"):
    return {
        "project": {"key": "PCI"},
        "issuetype": {"name": "Task"},
        "summary": summary,
        "status": {"name": status},
        "priority": {"name": "Low"},
        "labels": [],
        "components": [{"name": c} for c in (comps or [])],
        "customfield_10006": sp,
    }


def test_build_tree_filters_network_and_closed():
    # State of issues
    state = {
        "LVL2-1": {"_root": True, **_fields_lv12_feature()},
        # Children via Parent Link
        "PCI-EPIC-N": _fields_pci_epic(comps=["Network"]),
        "PCI-EPIC-C": _fields_pci_epic(comps=["Compute"]),
        "PCI-STORY": _fields_pci_task(comps=["Network"], sp=3),
        # Children of PCI-EPIC-N via Epic Link
        "PCI-TS1": _fields_pci_task(comps=["Network"], sp=5),
        "PCI-TS2": _fields_pci_task(comps=["Network"], sp=2, status="Done"),
    }
    edges_parent = {
        "LVL2-1": ["PCI-EPIC-N", "PCI-EPIC-C", "PCI-STORY"],
    }
    edges_epic = {
        "PCI-EPIC-N": ["PCI-TS1", "PCI-TS2"],
    }

    repo = RepoWithSearch(state, edges_parent, edges_epic)

    # skip_closed=False should include all except non-network epic (PCI-EPIC-C)
    tree = build_lsd_tree(repo, year="26", quarter="1", squad="Network", skip_closed=False)
    keys = [node.data.key for node in tree]
    assert "LVL2-1" in keys
    assert "PCI-EPIC-N" in keys
    assert "PCI-EPIC-C" not in keys  # filtered (not Network)
    assert "PCI-STORY" in keys
    assert "PCI-TS1" in keys
    assert "PCI-TS2" in keys  # included because skip_closed=False

    # skip_closed=True should exclude closed PCI issues (PCI-TS2)
    tree2 = build_lsd_tree(repo, year="26", quarter="1", squad="Network", skip_closed=True)
    keys2 = [node.data.key for node in tree2]
    assert "PCI-TS2" not in keys2

