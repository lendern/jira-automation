from lsd.fields import _to_python_value, FieldType


def test_coerce_int():
    """Le test vérifie que les INT sont correctement convertis et que None/valeurs invalides donnent 0."""
    assert _to_python_value(FieldType.INT, None) == 0
    assert _to_python_value(FieldType.INT, "5") == 5
    assert _to_python_value(FieldType.INT, "x") == 0


def test_coerce_float():
    """Le test vérifie que les FLOAT sont correctement convertis et que None/valeurs invalides donnent 0.0."""
    assert _to_python_value(FieldType.FLOAT, None) == 0.0
    assert _to_python_value(FieldType.FLOAT, "1.5") == 1.5
    assert _to_python_value(FieldType.FLOAT, "x") == 0.0


def test_coerce_str():
    """Le test vérifie que les STR sont convertis en chaîne et que None devient une chaîne vide."""
    assert _to_python_value(FieldType.STR, None) == ""
    assert _to_python_value(FieldType.STR, 10) == "10"


def test_coerce_labels_and_list_str():
    """Le test vérifie que LIST_STR/LABELS sont normalisés en list[str] avec des valeurs de repli cohérentes."""
    # labels
    assert _to_python_value(FieldType.LABELS, None) == []
    assert _to_python_value(FieldType.LABELS, []) == []
    assert _to_python_value(FieldType.LABELS, ["A", 1]) == ["A", "1"]
    assert _to_python_value(FieldType.LABELS, "A") == ["A"]
    # list_str behaves the same
    assert _to_python_value(FieldType.LIST_STR, None) == []
    assert _to_python_value(FieldType.LIST_STR, [1, "a"]) == ["1", "a"]
    assert _to_python_value(FieldType.LIST_STR, "x") == ["x"]
