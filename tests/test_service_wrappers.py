import pytest

from lsd.services import read_issue_field, update_issue_field


def test_read_issue_field_returns_logical_value(repo):
    """Le test vérifie que la lecture via le wrapper renvoie la valeur logique attendue."""
    key = "PCI-W1"
    # Seed raw shape as Jira would return
    repo.update_fields(key, {"priority": {"name": "Medium"}})
    assert read_issue_field(repo, key, "priority") == "Medium"


def test_read_issue_field_raises_unknown(repo):
    """Le test vérifie qu'une erreur est levée pour un champ logique inconnu."""
    with pytest.raises(KeyError):
        read_issue_field(repo, "PCI-W2", "not_exists")


def test_update_issue_field_merge_and_replace(repo):
    """Le test vérifie le merge sans doublon et le remplacement intégral via update_issue_field."""
    key = "PCI-W3"
    # Seed one label
    repo.update_fields(key, {"labels": ["FY26Q1"]})

    # Merge adds without duplicates
    update_issue_field(repo, key, "labels", ["FY26Q1", "FY26Q2"], merge=True)
    labels = read_issue_field(repo, key, "labels")
    assert sorted(labels) == ["FY26Q1", "FY26Q2"]

    # Replace overwrites
    update_issue_field(repo, key, "labels", ["Z"], merge=False)
    assert read_issue_field(repo, key, "labels") == ["Z"]


def test_update_issue_field_raises_on_readonly(repo):
    """Le test vérifie qu'une mise à jour d'un champ en lecture seule échoue."""
    with pytest.raises(ValueError):
        update_issue_field(repo, "PCI-W4", "status", "In Progress")
