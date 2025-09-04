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

    def set_labels(self, key: str, labels: List[str]) -> None:
        ...

    def set_priority(self, key: str, name: str) -> None:
        ...

    def set_story_points(self, key: str, points: int) -> None:
        ...

