from lsd.tree_builder import build_lsd_tree
from lsd.services import propagate_sprint


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

    def find_pci_keys_with_label_and_squad(self, label: str, squad: str):
        out = []
        for k, v in self.state.items():
            labels = v.get("labels") or []
            if label in labels:
                out.append(k)
        return out

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


def _fields_pci_issue(itype="Task", comps=None, status="To Do"):
    return {
        "project": {"key": "PCI"},
        "issuetype": {"name": itype},
        "summary": itype.lower(),
        "status": {"name": status},
        "priority": {"name": "Low"},
        "labels": [],
        "components": [{"name": c} for c in (comps or [])],
    }


def build_repo_for_sprint():
    state = {
        "LVL2-1": _fields_lv12_feature(),
        # Children under feature
        "PCI-EPIC": _fields_pci_issue("Epic", comps=["Network"]),
        "PCI-T1": _fields_pci_issue("Task", comps=["Network"]),
        "PCI-DONE": _fields_pci_issue("Task", comps=["Network"], status="Done"),
    }
    edges_parent = {"LVL2-1": ["PCI-EPIC", "PCI-T1", "PCI-DONE"]}
    edges_epic = {"PCI-EPIC": []}
    return Repo(state, edges_parent, edges_epic, lvl2_roots=["LVL2-1"])


def test_propagate_sprint_idempotent_when_label_present():
    """Le test vérifie qu'aucune mise à jour n'est émise si le label du sprint est déjà présent."""
    repo = build_repo_for_sprint()
    # Seed label FY26Q1 on all non-closed items
    repo.update_fields("PCI-EPIC", {"labels": ["FY26Q1"]})
    repo.update_fields("PCI-T1", {"labels": ["FY26Q1"]})
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=False)
    before = len(repo.updates)
    propagate_sprint(tree, "26", "1", repo)
    after = len(repo.updates)
    # No extra updates since label already present
    assert after == before


def test_propagate_sprint_respects_skip_closed_true():
    """Le test vérifie que l'option skip_closed empêche l'ajout du label aux tickets fermés."""
    repo = build_repo_for_sprint()
    tree = build_lsd_tree(repo, "26", "1", "Network", skip_closed=True)
    propagate_sprint(tree, "26", "1", repo)
    # Closed issue should remain without the label
    assert (repo.state["PCI-DONE"].get("labels") or []) == []
