from lsd.tree_builder import build_lsd_tree


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


def test_build_tree_no_roots_returns_empty():
    """Le test vérifie qu'un arbre vide est retourné quand aucune racine LVL2 n'est trouvée."""
    state = {}
    repo = Repo(state, edges_parent={}, edges_epic={}, lvl2_roots=[])
    tree = build_lsd_tree(repo, year="26", quarter="1", squad="Network", skip_closed=False)
    keys = [node.data.key for node in tree]
    assert keys == []


def test_build_tree_multiple_roots_traversal_complete():
    """Le test vérifie que l'arbre couvre plusieurs racines et tous leurs enfants sans doublons."""
    state = {
        "LVL2-1": _fields_lv12_feature("feat1"),
        "LVL2-2": _fields_lv12_feature("feat2"),
        "PCI-E1": _fields_pci_issue("Epic", comps=["Network"]),
        "PCI-T1": _fields_pci_issue("Task", comps=["Network"]),
        "PCI-E2": _fields_pci_issue("Epic", comps=["Network"]),
        "PCI-T2": _fields_pci_issue("Task", comps=["Network"]),
    }
    edges_parent = {
        "LVL2-1": ["PCI-E1", "PCI-T1"],
        "LVL2-2": ["PCI-E2", "PCI-T2"],
    }
    edges_epic = {}
    repo = Repo(state, edges_parent=edges_parent, edges_epic=edges_epic, lvl2_roots=["LVL2-1", "LVL2-2"])
    tree = build_lsd_tree(repo, year="26", quarter="1", squad="Network", skip_closed=False)
    keys = [node.data.key for node in tree]
    # Ensure both roots and all children are present (6 nodes total)
    assert set(keys) == {"LVL2-1", "LVL2-2", "PCI-E1", "PCI-T1", "PCI-E2", "PCI-T2"}
    assert len(keys) == 6
