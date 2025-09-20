def str_lvl2_sprint_label(s_year: str, s_quarter: str) -> str:
    """Return LVL2 sprint label like 'SD-FY{year}-Q{quarter}'."""
    return f'SD-FY{s_year}-Q{s_quarter}'


def str_lvl3_sprint_label(s_year: str, s_quarter: str) -> str:
    """Return LVL3 sprint label like 'FY{year}Q{quarter}'."""
    return f'FY{s_year}Q{s_quarter}'

