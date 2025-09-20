from lsd.fields import read_field, update_field


def test_labels_merge_single_idempotent(repo):
    """Le test vérifie que la fusion d'un label identique n'émet aucune mise à jour."""
    key = "PCI-L1"
    # Seed with one label
    repo.update_fields(key, {"labels": ["Z"]})
    n = len(repo.updates)
    # Merge a scalar identical value -> no-op
    update_field(repo, key, "labels", "Z", merge=True)
    assert len(repo.updates) == n


def test_labels_replace_entirely(repo):
    """Le test vérifie que le mode remplacement écrase complètement la liste des labels."""
    key = "PCI-L2"
    repo.update_fields(key, {"labels": ["A"]})
    update_field(repo, key, "labels", ["B", "C"], merge=False)
    assert read_field(repo, key, "labels") == ["B", "C"]


def test_components_scalar_promotion_and_idempotent(repo):
    """Le test vérifie la promotion d'un scalaire en liste pour components et l'idempotence des mises à jour."""
    key = "PCI-C1"
    # Initially no components
    assert read_field(repo, key, "components") == []
    # Provide scalar -> promoted to list and mapped to dict payload
    update_field(repo, key, "components", "Network")
    assert read_field(repo, key, "components") == ["Network"]
    n = len(repo.updates)
    # Idempotent re-apply
    update_field(repo, key, "components", "Network")
    assert len(repo.updates) == n
