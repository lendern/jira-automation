import pytest

from lsd.tree_builder import build_lsd_tree
from lsd.services import aggregate_points


class Repo:
    def __init__(self, state, edges_parent, edges_epic, lvl2_roots):
        self.state = state
        self.edges_parent = edges_parent
        self.edges_epic = edges_epic
        self.lvl2_roots = lvl2_roots
        self.updates = []

    # Reads used by tree_builder/services
    def get_issue(self, key: str):
        from tests.conftest import FakeIssue

        return FakeIssue(key, self.state.get(key, {}))

    def find_lvl2_new_features(self, sprint: str, squad: str):
        return list(self.lvl2_roots)

    def find_pci_children_by_parent_link(self, parent_key: str):
        return list(self.edges_parent.get(parent_key, []))

    def find_children_by_epic_link(self, epic_key: str, squad: str):
        return list(self.edges_epic.get(epic_key, []))

    # Generic fields
    def get_fields(self, key: str, fields: list[str]):
        from tests.conftest import _wrap_value
        cur = self.state.get(key, {})
        return {f: _wrap_value(cur.get(f)) for f in fields}

    def update_fields(self, key: str, fields: dict[str, object]):
        box = self.state.setdefault(key, {})
        box.update(fields)
        self.updates.append((key, fields))


def _fields_lv12_feature(summary="feat"):
    return {
        "project": {"key": "LVL2"},
        "issuetype": {"name": "New Feature"},
        "summary": summary,
        "status": {"name": "Open"},
        "priority": {"name": "Medium"},
        "labels": [],
    }


def _fields_pci_epic(comps=None, sp=None, status="To Do", prio="High"):
    return {
        "project": {"key": "PCI"},
        "issuetype": {"name": "Epic"},
        "summary": "pci epic",
        "status": {"name": status},
        "priority": {"name": prio},
        "labels": [],
        "components": [{"name": c} for c in (comps or [])],
        "customfield_10006": sp,
    }


def _fields_pci_task(comps=None, sp=None, status="To Do", prio="Low"):
    return {
        "project": {"key": "PCI"},
        "issuetype": {"name": "Task"},
        "summary": "task",
        "status": {"name": status},
        "priority": {"name": prio},
        "labels": [],
        "components": [{"name": c} for c in (comps or [])],
        "customfield_10006": sp,
    }


def build_repo_for_agg():
    state = {
        "LVL2-1": _fields_lv12_feature(),
        # Children
        "PCI-EPIC": _fields_pci_epic(comps=["Network"], sp=0, prio="High"),
        # Direct child under epic
        "PCI-T2": _fields_pci_task(comps=["Network"], sp=5, prio="Medium"),
    }
    edges_parent = {"LVL2-1": ["PCI-EPIC"]}
    edges_epic = {"PCI-EPIC": ["PCI-T2"]}
    return Repo(state, edges_parent, edges_epic, lvl2_roots=["LVL2-1"])


def test_aggregate_points_raises_if_epic_not_in_tree():
    """Le test vérifie qu'une erreur est levée si l'Épic ciblé est absent de l'arbre."""
    repo = build_repo_for_agg()
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=False)
    with pytest.raises(KeyError):
        aggregate_points(tree, "PCI-NOPE", repo)


def test_aggregate_points_idempotent_update():
    """Le test vérifie que le calcul met à jour l'Épic et reste idempotent si le total ne change pas."""
    repo = build_repo_for_agg()
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=False)
    total = aggregate_points(tree, "PCI-EPIC", repo)
    assert total == 5
    assert repo.state["PCI-EPIC"]["customfield_10006"] == 5
    n = len(repo.updates)
    # Re-run: no additional update since total unchanged
    total2 = aggregate_points(tree, "PCI-EPIC", repo)
    assert total2 == 5
    assert len(repo.updates) == n
