import pytest

from lsd.fields import read_field, update_field


def test_story_points_read_write_idempotent(repo):
    key = "PCI-1"
    # no value => coerces to 0
    assert read_field(repo, key, "story_points") == 0

    # set to 8
    update_field(repo, key, "story_points", 8)
    assert repo.state[key]["customfield_10006"] == 8
    assert read_field(repo, key, "story_points") == 8
    updates_len = len(repo.updates)

    # setting same value should be idempotent (no new update)
    update_field(repo, key, "story_points", 8)
    assert len(repo.updates) == updates_len


def test_labels_merge_and_replace(repo):
    key = "PCI-2"
    # start with label FY26Q1
    repo.state[key] = {"labels": ["FY26Q1"]}
    # merge existing + FY26Q2 (idempotent for duplicates)
    update_field(repo, key, "labels", ["FY26Q1", "FY26Q2"], merge=True)
    assert sorted(repo.state[key]["labels"]) == ["FY26Q1", "FY26Q2"]

    # replace with Z only
    update_field(repo, key, "labels", ["Z"], merge=False)
    assert repo.state[key]["labels"] == ["Z"]


def test_priority_transform(repo):
    key = "PCI-3"
    repo.state[key] = {"priority": {"name": "High"}}
    assert read_field(repo, key, "priority") == "High"

    # update to Highest
    update_field(repo, key, "priority", "Highest")
    assert repo.state[key]["priority"] == {"name": "Highest"}

    # idempotent
    n = len(repo.updates)
    update_field(repo, key, "priority", "Highest")
    assert len(repo.updates) == n


def test_components_transform(repo):
    key = "PCI-4"
    repo.state[key] = {"components": [{"name": "Network"}]}
    assert read_field(repo, key, "components") == ["Network"]

    # Add Compute as well
    update_field(repo, key, "components", ["Network", "Compute"])
    assert sorted(d["name"] for d in repo.state[key]["components"]) == ["Compute", "Network"]

    # Idempotent when same names, any order
    m = len(repo.updates)
    update_field(repo, key, "components", ["Compute", "Network"])
    assert len(repo.updates) == m


def test_status_readonly_raises_on_update(repo):
    key = "PCI-5"
    repo.state[key] = {"status": {"name": "Done"}}
    assert read_field(repo, key, "status") == "Done"
    with pytest.raises(ValueError):
        update_field(repo, key, "status", "In Progress")


def test_lv12_pu_blfnt(repo):
    feat = "LVL2-10"
    epic = "LVL2-20"

    # Initially None
    assert read_field(repo, feat, "pu") is None
    assert read_field(repo, epic, "blfnt") is None

    update_field(repo, feat, "pu", "MyUnit")
    update_field(repo, epic, "blfnt", "MyBLFNT")
    assert repo.state[feat]["customfield_16708"] == {"value": "MyUnit"}
    assert repo.state[epic]["customfield_10530"] == {"value": "MyBLFNT"}

    # Re-apply same: idempotent
    cnt = len(repo.updates)
    update_field(repo, feat, "pu", "MyUnit")
    update_field(repo, epic, "blfnt", "MyBLFNT")
    assert len(repo.updates) == cnt


def test_unknown_field_raises(repo):
    with pytest.raises(KeyError):
        read_field(repo, "PCI-6", "not_exists")
    with pytest.raises(KeyError):
        update_field(repo, "PCI-6", "not_exists", 1)

