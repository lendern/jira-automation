from lsd.tree_builder import build_lsd_tree, iter_lvl2_keys


class Repo:
    def __init__(self, state, edges_parent, edges_epic, lvl2_roots):
        self.state = state
        self.edges_parent = edges_parent
        self.edges_epic = edges_epic
        self.lvl2_roots = lvl2_roots

    # Minimal read API used by tree_builder
    def get_issue(self, key: str):
        from tests.conftest import FakeIssue

        return FakeIssue(key, self.state.get(key, {}))

    def find_lvl2_new_features(self, sprint: str, squad: str):
        return list(self.lvl2_roots)

    def find_pci_children_by_parent_link(self, parent_key: str):
        return list(self.edges_parent.get(parent_key, []))

    def find_children_by_epic_link(self, epic_key: str, squad: str):
        return list(self.edges_epic.get(epic_key, []))


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


def test_iter_lvl2_keys_returns_only_lvl2_roots_and_items():
    """Le test vérifie que l'itérateur retourne uniquement les clés des items LVL2 présents dans l'arbre."""
    state = {
        "LVL2-1": _fields_lv12_feature("feat1"),
        "LVL2-2": _fields_lv12_feature("feat2"),
        # Children under features
        "PCI-E1": _fields_pci_issue("Epic", comps=["Network"]),
        "PCI-T1": _fields_pci_issue("Task", comps=["Network"]),
        "PCI-E2": _fields_pci_issue("Epic", comps=["Network"]),
        "PCI-T2": _fields_pci_issue("Task", comps=["Network"]),
    }
    edges_parent = {
        "LVL2-1": ["PCI-E1", "PCI-T1"],
        "LVL2-2": ["PCI-E2", "PCI-T2"],
    }
    repo = Repo(state, edges_parent=edges_parent, edges_epic={}, lvl2_roots=["LVL2-1", "LVL2-2"])
    tree = build_lsd_tree(repo, year="26", quarter="1", squad="Network", skip_closed=False)

    keys = list(iter_lvl2_keys(tree))
    assert set(keys) == {"LVL2-1", "LVL2-2"}
