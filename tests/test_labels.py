from lsd.labels import str_lvl2_sprint_label, str_lvl3_sprint_label


def test_str_lvl2_sprint_label():
    """Le test vérifie que l'étiquette LVL2 du sprint est correctement formatée."""
    assert str_lvl2_sprint_label("26", "1") == "SD-FY26-Q1"
    assert str_lvl2_sprint_label("27", "4") == "SD-FY27-Q4"


def test_str_lvl3_sprint_label():
    """Le test vérifie que l'étiquette LVL3 du sprint est correctement formatée."""
    assert str_lvl3_sprint_label("26", "1") == "FY26Q1"
    assert str_lvl3_sprint_label("27", "3") == "FY27Q3"
