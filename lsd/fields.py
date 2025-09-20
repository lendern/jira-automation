from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class FieldType(str, Enum):
    INT = "int"
    FLOAT = "float"
    STR = "str"
    LIST_STR = "list_str"
    LABELS = "labels"  # alias of list[str] with merge semantics


@dataclass(frozen=True)
class CustomFieldSpec:
    name: str
    jira_id: str  # e.g., "customfield_10006" or "labels"
    ftype: FieldType


# Initial registry: extend as needed
FIELD_REGISTRY: Dict[str, CustomFieldSpec] = {
    # Jira default for story points commonly used by Jira Cloud
    "story_points": CustomFieldSpec(
        name="story_points", jira_id="customfield_10006", ftype=FieldType.INT
    ),
    # Built-in labels field
    "labels": CustomFieldSpec(
        name="labels", jira_id="labels", ftype=FieldType.LABELS
    ),
}


def _coerce_in(ftype: FieldType, raw: Any) -> Any:
    if ftype == FieldType.INT:
        try:
            return int(raw) if raw is not None else 0
        except Exception:
            return 0
    if ftype == FieldType.FLOAT:
        try:
            return float(raw) if raw is not None else 0.0
        except Exception:
            return 0.0
    if ftype == FieldType.STR:
        return str(raw) if raw is not None else ""
    if ftype in (FieldType.LIST_STR, FieldType.LABELS):
        if not raw:
            return []
        if isinstance(raw, list):
            return [str(x) for x in raw]
        # Single value promoted to list
        return [str(raw)]
    return raw


def _normalize_list_str(values: List[str]) -> List[str]:
    return sorted({str(v) for v in (values or [])})


def read_field(repo, issue_key: str, name: str) -> Any:
    """Read a logical field by name using the repository and registry.

    Returns a Python-typed value according to the field spec.
    """
    spec = FIELD_REGISTRY.get(name)
    if not spec:
        raise KeyError(f"Unknown field name: {name}")
    raw = repo.get_fields(issue_key, [spec.jira_id]).get(spec.jira_id)
    return _coerce_in(spec.ftype, raw)


def update_field(repo, issue_key: str, name: str, value: Any, *, merge: bool = False) -> None:
    """Update a logical field by name.

    - For scalar fields (INT/FLOAT/STR): set if changed.
    - For LIST_STR/LABELS:
        - merge=True: add items idempotently (union) sans duplication
        - merge=False: remplacer intégralement
    """
    spec = FIELD_REGISTRY.get(name)
    if not spec:
        raise KeyError(f"Unknown field name: {name}")

    if spec.ftype in (FieldType.LIST_STR, FieldType.LABELS):
        new_list = _normalize_list_str(value if isinstance(value, list) else [value])
        if merge:
            current = read_field(repo, issue_key, name) or []
            merged = _normalize_list_str(list(current) + list(new_list))
            repo.update_fields(issue_key, {spec.jira_id: merged})
        else:
            repo.update_fields(issue_key, {spec.jira_id: new_list})
        return

    # Scalars
    desired = _coerce_in(spec.ftype, value)
    repo.update_fields(issue_key, {spec.jira_id: desired})

