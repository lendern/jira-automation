import logging
from typing import List, Any

from .ports import Repository


logger = logging.getLogger(__name__)


class SimRepository(Repository):
    """Repository wrapper that simulates updates by logging instead of mutating.

    All read/search operations are delegated to the wrapped repository.
    Only `update_fields` is intercepted to avoid side effects in simulation mode.
    """

    def __init__(self, wrapped: Repository) -> None:
        self._wrapped = wrapped

    # ---------------
    # Reads / search
    # ---------------
    def get_issue(self, key: str) -> Any:
        return self._wrapped.get_issue(key)

    def find_lvl2_new_features(self, sprint: str, squad: str) -> List[str]:
        return self._wrapped.find_lvl2_new_features(sprint, squad)

    def find_pci_children_by_parent_link(self, parent_key: str) -> List[str]:
        return self._wrapped.find_pci_children_by_parent_link(parent_key)

    def find_children_by_epic_link(self, epic_key: str, squad: str) -> List[str]:
        return self._wrapped.find_children_by_epic_link(epic_key, squad)

    def find_pci_keys_with_label_and_squad(self, label: str, squad: str) -> List[str]:
        return self._wrapped.find_pci_keys_with_label_and_squad(label, squad)

    # ---------------
    # Generic field access
    # ---------------
    def get_fields(self, key: str, fields: List[str]) -> dict[str, Any]:
        return self._wrapped.get_fields(key, fields)

    def update_fields(self, key: str, fields: dict[str, Any]) -> None:
        # NOTE about field transforms (in_transform / out_transform):
        # - The logical field abstraction (lsd/fields.py) defines CustomFieldSpec with
        #   optional `in_transform` and `out_transform` functions to convert between
        #   Jira shapes (dicts/objects) and simple Python values.
        # - Reads: read_field() applies `in_transform(raw)` (e.g., {"name": "High"} -> "High").
        # - Writes: update_field() applies `out_transform(value)` to build the final Jira payload
        #   passed here (e.g., "UnitX" -> {"value": "UnitX"}). In simulation mode we therefore
        #   log the exact payload that would be sent to Jira after transformation.
        #   Example: for a custom select stored under `value`:
        #       FIELD_REGISTRY["pu"] = CustomFieldSpec(..., in_transform=lambda r: getattr(r, "value", None),
        #                                              out_transform=lambda v: {"value": v} if v is not None else None)
        #       read_field(repo, "LVL2-1", "pu")            # -> "UnitX" when Jira returns {"value": "UnitX"}
        #       update_field(repo, "LVL2-1", "pu", "UnitY")  # -> calls update_fields with {"customfield_16708": {"value": "UnitY"}}
        #   Here we only log that payload to avoid side effects in simulation mode.
        if not fields:
            return
        pretty = ", ".join(f"{k}={v!r}" for k, v in fields.items())
        logger.info("[SIMU] skip update for %s: %s", key, pretty)
