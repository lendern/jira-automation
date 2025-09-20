from typing import Protocol, List, Any


class Repository(Protocol):
    def get_issue(self, key: str) -> Any:
        ...

    def find_lvl2_new_features(self, sprint: str, squad: str) -> List[str]:
        ...

    def find_pci_children_by_parent_link(self, parent_key: str) -> List[str]:
        ...

    def find_children_by_epic_link(self, epic_key: str, squad: str) -> List[str]:
        ...

    def find_pci_keys_with_label_and_squad(self, label: str, squad: str) -> List[str]:
        ...

    # Generic field access (productizing customfields)
    def get_fields(self, key: str, fields: List[str]) -> dict[str, Any]:
        ...

    def update_fields(self, key: str, fields: dict[str, Any]) -> None:
        ...
