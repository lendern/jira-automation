from lsd.status import jql_not_closed, CLOSED_STATUSES


def test_jql_not_closed_default_field():
    frag = jql_not_closed()
    # Order should match tuple order
    expected = 'status NOT IN (' + ", ".join(f'"{s}"' for s in CLOSED_STATUSES) + ')'
    assert frag == expected


def test_jql_not_closed_custom_field():
    frag = jql_not_closed('myStatus')
    expected = 'myStatus NOT IN (' + ", ".join(f'"{s}"' for s in CLOSED_STATUSES) + ')'
    assert frag == expected

