from lsd.tree_builder import build_lsd_tree
from lsd.services import (
    propagate_sprint,
    propagate_priority,
    find_orphans,
    aggregate_points,
    update_lvl2_pu,
    update_lvl2_blfnt,
    read_issue_field,
    update_issue_field,
)


class ServiceRepo:
    def __init__(self, state, edges_parent, edges_epic, lvl2_roots):
        self.state = state
        self.edges_parent = edges_parent
        self.edges_epic = edges_epic
        self.lvl2_roots = lvl2_roots

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

    def find_pci_keys_with_label_and_squad(self, label: str, squad: str):
        out = []
        for k, v in self.state.items():
            labels = v.get("labels") or []
            if label in labels and (v.get("components") is None or {d.get("name") for d in v.get("components", [])}):
                out.append(k)
        return out

    # Generic fields
    def get_fields(self, key: str, fields: list[str]):
        # Emulate Jira objects by wrapping dicts/lists to provide attribute access
        from tests.conftest import _wrap_value
        cur = self.state.get(key, {})
        return {f: _wrap_value(cur.get(f)) for f in fields}

    def update_fields(self, key: str, fields: dict[str, object]):
        box = self.state.setdefault(key, {})
        box.update(fields)


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


def _fields_pci_epic(priority="High", comps=None, sp=None, status="To Do"):
    return {
        "project": {"key": "PCI"},
        "issuetype": {"name": "Epic"},
        "summary": "pci epic",
        "status": {"name": status},
        "priority": {"name": priority},
        "labels": [],
        "components": [{"name": c} for c in (comps or [])],
        "customfield_10006": sp,
    }


def _fields_pci_task(priority="Low", comps=None, sp=None, status="To Do"):
    return {
        "project": {"key": "PCI"},
        "issuetype": {"name": "Task"},
        "summary": "task",
        "status": {"name": status},
        "priority": {"name": priority},
        "labels": [],
        "components": [{"name": c} for c in (comps or [])],
        "customfield_10006": sp,
    }


def build_sample_repo():
    state = {
        "LVL2-1": _fields_lv12_feature(),
        # Children
        "PCI-EPIC": _fields_pci_epic(priority="High", comps=["Network"], sp=0),
        "PCI-T1": _fields_pci_task(priority="Low", comps=["Network"], sp=3),
        "PCI-T2": _fields_pci_task(priority="Medium", comps=["Network"], sp=5),
        "PCI-DONE": _fields_pci_task(priority="Low", comps=["Network"], sp=2, status="Done"),
        # Orphan candidate
        "PCI-ORPH": _fields_pci_task(priority="Low", comps=["Network"], sp=1),
    }
    edges_parent = {"LVL2-1": ["PCI-EPIC", "PCI-T1", "PCI-DONE"]}
    edges_epic = {"PCI-EPIC": ["PCI-T2"]}
    repo = ServiceRepo(state, edges_parent, edges_epic, lvl2_roots=["LVL2-1"])
    return repo


def test_propagate_sprint_adds_label_only_to_non_closed():
    repo = build_sample_repo()
    tree = build_lsd_tree(repo, year="26", quarter="1", squad="Network", skip_closed=False)
    propagate_sprint(tree, "26", "1", repo)
    assert "FY26Q1" in (repo.state["PCI-EPIC"].get("labels") or [])
    assert "FY26Q1" in (repo.state["PCI-T1"].get("labels") or [])
    assert "FY26Q1" in (repo.state["PCI-T2"].get("labels") or [])
    # closed task should remain unchanged
    assert (repo.state["PCI-DONE"].get("labels") or []) == []


def test_propagate_priority_from_epic_to_children():
    repo = build_sample_repo()
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=False)
    propagate_priority(tree, repo)
    assert repo.state["PCI-T1"]["priority"]["name"] == "High"
    assert repo.state["PCI-T2"]["priority"]["name"] == "High"
    # closed child should not change
    assert repo.state["PCI-DONE"]["priority"]["name"] == "Low"


def test_find_orphans_returns_only_outside_tree():
    repo = build_sample_repo()
    # Mark an in-tree issue with the quarter label
    repo.state["PCI-T1"]["labels"] = ["FY26Q1"]
    # Mark a true orphan as well
    repo.state["PCI-ORPH"]["labels"] = ["FY26Q1"]
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=False)
    orphans = find_orphans(tree, "26", "1", "Network", repo)
    keys = {o.key for o in orphans}
    assert "PCI-ORPH" in keys
    assert "PCI-T1" not in keys


def test_aggregate_points_updates_epic():
    repo = build_sample_repo()
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=False)
    total = aggregate_points(tree, "PCI-EPIC", repo)
    assert total == 5  # only direct child PCI-T2 is under epic
    assert repo.state["PCI-EPIC"]["customfield_10006"] == 5


def test_update_read_lvl2_fields():
    repo = build_sample_repo()
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=False)
    update_lvl2_pu(tree, "LVL2-1", "UnitX", repo)
    update_lvl2_blfnt(tree, "LVL2-1", "BLFNTY", repo)  # this key is a feature; still accepted by abstraction
    assert repo.state["LVL2-1"]["customfield_16708"] == {"value": "UnitX"}
    assert repo.state["LVL2-1"]["customfield_10530"] == {"value": "BLFNTY"}


def test_read_update_issue_field_wrappers():
    repo = build_sample_repo()
    assert read_issue_field(repo, "PCI-EPIC", "priority") == "High"
    update_issue_field(repo, "PCI-EPIC", "priority", "Highest")
    assert read_issue_field(repo, "PCI-EPIC", "priority") == "Highest"
