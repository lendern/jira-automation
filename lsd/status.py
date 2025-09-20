"""Centralized status constants and helpers."""

CLOSED_STATUSES = (
    "Done",
    "To Prod",
    "Cancelled",
    "Canceled",
    "Closed",
)


def jql_not_closed(field: str = "status") -> str:
    """Return a JQL snippet excluding closed statuses.

    Example: status NOT IN ("Done", "To Prod", ...)
    """
    values = ", ".join(f'"{s}"' for s in CLOSED_STATUSES)
    return f"{field} NOT IN ({values})"

