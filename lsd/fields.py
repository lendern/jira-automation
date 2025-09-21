from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


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
    readable: bool = True
    writable: bool = True
    in_transform: Optional[Callable[[Any], Any]] = None
    out_transform: Optional[Callable[[Any], Any]] = None


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
    # Priority by name
    "priority": CustomFieldSpec(
        name="priority",
        jira_id="priority",
        ftype=FieldType.STR,
        in_transform=lambda raw: getattr(raw, "name", None),
        out_transform=lambda v: {"name": v} if v is not None else None,
    ),
    # Components (list of names)
    "components": CustomFieldSpec(
        name="components",
        jira_id="components",
        ftype=FieldType.LIST_STR,
        in_transform=lambda raw: [getattr(c, "name", "") for c in (raw or [])],
        out_transform=lambda vs: [{"name": str(v)} for v in (vs or [])],
    ),
    # Summary (title)
    "summary": CustomFieldSpec(
        name="summary", jira_id="summary", ftype=FieldType.STR
    ),
    # Status (read-only via fields; transitions are separate API)
    "status": CustomFieldSpec(
        name="status",
        jira_id="status",
        ftype=FieldType.STR,
        readable=True,
        writable=False,
        in_transform=lambda raw: getattr(raw, "name", None),
    ),
    # Project key (read-only)
    "project": CustomFieldSpec(
        name="project",
        jira_id="project",
        ftype=FieldType.STR,
        readable=True,
        writable=False,
        in_transform=lambda raw: getattr(raw, "key", None),
    ),
    # Issue type name (read-only)
    "issue_type": CustomFieldSpec(
        name="issue_type",
        jira_id="issuetype",
        ftype=FieldType.STR,
        readable=True,
        writable=False,
        in_transform=lambda raw: getattr(raw, "name", None),
    ),
    # LVL2 specific custom fields
    # PU (Unit) select field on LVL2 Features
    "pu": CustomFieldSpec(
        name="pu",
        jira_id="customfield_16708",
        ftype=FieldType.STR,
        in_transform=lambda raw: getattr(raw, "value", None),
        out_transform=lambda v: {"value": v} if v is not None else None,
    ),
    # BLFNT select field on LVL2 Epics
    "blfnt": CustomFieldSpec(
        name="blfnt",
        jira_id="customfield_10530",
        ftype=FieldType.STR,
        in_transform=lambda raw: getattr(raw, "value", None),
        out_transform=lambda v: {"value": v} if v is not None else None,
    ),
}


class FieldAccessMixin:
    """Lightweight mixin to access logical fields on an Issue via a Repository.

    Usage:
        issue.read_myfield(repo, "priority")
        issue.update_myfield(repo, "labels", ["FY26Q2"], merge=True)
    """

    key: str  # expected attribute on host class

    def read_myfield(self, repo, name: str) -> Any:
        return read_field(repo, self.key, name)

    def update_myfield(self, repo, name: str, value: Any, *, merge: bool = False) -> None:
        update_field(repo, self.key, name, value, merge=merge)


def _to_python_value(ftype: FieldType, raw: Any) -> Any:
    """Convertit une valeur brute en valeur Python selon le `FieldType`.

    Cette fonction est utilisée côté lecture lorsqu'aucune `in_transform` n'est
    définie dans la spécification du champ. Elle applique des conversions
    tolérantes avec des valeurs de repli pour éviter les exceptions.

    Paramètres:
    - ftype: type logique du champ (INT, FLOAT, STR, LIST_STR, LABELS).
    - raw: valeur brute renvoyée par l'API Jira (ou `None`).

    Retour:
    - INT: `int(raw)`; `0` si `raw` est `None` ou convertible invalide.
    - FLOAT: `float(raw)`; `0.0` si `raw` est `None` ou convertible invalide.
    - STR: `str(raw)`; chaîne vide si `raw` est `None`.
    - LIST_STR / LABELS:
        - `[]` si `raw` est falsy (`None`, `[]`, etc.).
        - si `raw` est une liste, chaque élément est converti en `str`.
        - sinon, promotion en liste à un élément `[str(raw)]`.
    - Autres types: valeur `raw` inchangée.
    """
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
    if spec.in_transform:
        return spec.in_transform(raw)
    return _to_python_value(spec.ftype, raw)


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
    if not spec.writable:
        raise ValueError(f"Field '{name}' is not writable")

    if spec.ftype in (FieldType.LIST_STR, FieldType.LABELS):
        new_list = _normalize_list_str(value if isinstance(value, list) else [value])
        current = read_field(repo, issue_key, name) or []
        desired = _normalize_list_str(list(current) + list(new_list)) if merge else new_list
        if desired == _normalize_list_str(current):
            return
        out_val = spec.out_transform(desired) if spec.out_transform else desired
        repo.update_fields(issue_key, {spec.jira_id: out_val})
        return

    # Scalars
    desired_typed = _to_python_value(spec.ftype, value) if not spec.in_transform else value
    current = read_field(repo, issue_key, name)
    if current == desired_typed:
        return
    out_val = spec.out_transform(desired_typed) if spec.out_transform else desired_typed
    repo.update_fields(issue_key, {spec.jira_id: out_val})
