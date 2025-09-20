from lsd.fields import FieldAccessMixin, read_field


class DummyIssue(FieldAccessMixin):
    def __init__(self, key: str):
        self.key = key


def test_read_myfield_delegates_and_converts(repo):
    """Le test vérifie que read_myfield délègue à l'abstraction et retourne la valeur logique."""
    key = "PCI-X"
    # seed raw priority shape
    repo.update_fields(key, {"priority": {"name": "High"}})
    d = DummyIssue(key)
    assert d.read_myfield(repo, "priority") == "High"
    # sanity: underlying read_field matches
    assert read_field(repo, key, "priority") == "High"


def test_update_myfield_sets_labels_with_merge(repo):
    """Le test vérifie le merge idempotent et le remplacement des labels via update_myfield."""
    key = "PCI-Y"
    d = DummyIssue(key)
    # initial: add single label
    d.update_myfield(repo, "labels", ["A"], merge=True)
    assert read_field(repo, key, "labels") == ["A"]
    # merge should union without duplicates
    d.update_myfield(repo, "labels", ["A", "B"], merge=True)
    assert sorted(read_field(repo, key, "labels")) == ["A", "B"]
    # replace entirely when merge=False
    d.update_myfield(repo, "labels", ["Z"], merge=False)
    assert read_field(repo, key, "labels") == ["Z"]
