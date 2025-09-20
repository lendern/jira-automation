import logging
from typing import List, Any

from jira import JIRA
from lsd.status import jql_not_closed


logger = logging.getLogger(__name__)


JQL_NOT_CLOSED = jql_not_closed()

# Base roots
JQL_LVL2_FOR_PCI_ROOT = 'project = LVL2 AND type = "New Feature"'
JQL_PCI_ROOT = 'project = PCI AND type in ("Epic", "Story", "Task")'

# Squad-specific filters (current scope targets Network)
JQL_NETWORK_PRODUCT_ONLY = '"OVH Product" in ("Public cloud Network - Floating IP (Neutron)", "Public cloud Network - Load Balancer (Octavia)", "Public cloud Network - Public & Private Network (Neutron)", "Public cloud Network - Public Gateway (Neutron)")'
JQL_NETWORK_CONTRIB_ONLY = '"Contributor(s) Squad(s) (Manual)" = "PU.pCI/Network"'
JQL_LVL2_NETWORK_ONLY = f'(({JQL_NETWORK_PRODUCT_ONLY}) OR ({JQL_NETWORK_CONTRIB_ONLY}))'


def _run_search(jira: JIRA, jql: str) -> List[Any]:
    logger.debug("JQL: %s", jql)
    return jira.search_issues(jql, fields="key", maxResults=False)


class JiraRepository:
    """Concrete repository backed by jira.JIRA client.

    Encapsulates all JIRA operations (search/read/update) to keep domain pure.
    """

    def __init__(self, client: JIRA) -> None:
        self._jira = client

    # -----------------
    # Reads
    # -----------------
    def get_issue(self, key: str) -> Any:
        return self._jira.issue(key)

    def find_lvl2_new_features(self, sprint: str, squad: str) -> List[str]:
        terms = [JQL_LVL2_FOR_PCI_ROOT, f"sprint = {sprint}", JQL_NOT_CLOSED]
        if squad == 'Network':
            terms.append(JQL_LVL2_NETWORK_ONLY)
        jql = ' AND '.join(terms) + ' ORDER BY priority DESC'
        issues = _run_search(self._jira, jql)
        return [i.key for i in issues]

    def find_pci_children_by_parent_link(self, parent_key: str) -> List[str]:
        # Match current logic used in LVL2feature.get_childs
        jql = (
            f'Project = PCI AND "Parent Link" = {parent_key} AND '
            f'type in (Epic, Story, Task) AND '
            f'(Component = "Network" OR labels = "Openstack_Networking") AND '
            f'{JQL_NOT_CLOSED} ORDER BY priority DESC'
        )
        issues = _run_search(self._jira, jql)
        return [i.key for i in issues]

    def find_children_by_epic_link(self, epic_key: str, squad: str) -> List[str]:
        # Match current logic used in PCIEpic.get_childs (filters to Network component)
        component_filter = 'Component = "Network"' if squad == 'Network' else ''
        filters = [f'"Epic Link" = {epic_key}', 'type in (Epic, Story, Task)']
        if component_filter:
            filters.append(component_filter)
        filters.append(JQL_NOT_CLOSED)
        jql = ' AND '.join(filters) + ' ORDER BY status'
        issues = _run_search(self._jira, jql)
        return [i.key for i in issues]

    def find_pci_keys_with_label_and_squad(self, label: str, squad: str) -> List[str]:
        filters = [JQL_PCI_ROOT, f'Component = {squad}', f'labels = "{label}"', JQL_NOT_CLOSED]
        jql = ' AND '.join(filters) + ' ORDER BY priority DESC'
        issues = _run_search(self._jira, jql)
        return [i.key for i in issues]

    # -----------------
    # Mutations
    # -----------------
    def set_labels(self, key: str, labels: List[str]) -> None:
        issue = self._jira.issue(key)
        current = list(getattr(issue.fields, 'labels', []) or [])
        new_labels = sorted(set(labels))
        if sorted(set(current)) == new_labels:
            logger.debug("labels unchanged for %s", key)
            return
        logger.info("update labels for %s: %s", key, new_labels)
        issue.update(fields={"labels": new_labels})

    def add_label(self, key: str, label: str) -> None:
        """Ensure a single label exists on the issue (idempotent)."""
        issue = self._jira.issue(key)
        current = list(getattr(issue.fields, 'labels', []) or [])
        if label in current:
            logger.debug("label '%s' already present on %s", label, key)
            return
        new_labels = sorted(set(current + [label]))
        logger.info("add label for %s: %s", key, label)
        issue.update(fields={"labels": new_labels})

    def set_priority(self, key: str, name: str) -> None:
        issue = self._jira.issue(key)
        current = getattr(issue.fields, 'priority', None)
        current_name = getattr(current, 'name', None)
        if current_name == name:
            logger.debug("priority unchanged for %s (%s)", key, name)
            return
        logger.info("set priority for %s: %s", key, name)
        issue.update(fields={"priority": {"name": name}})

    def set_story_points(self, key: str, points: int) -> None:
        if not isinstance(points, int) or points < 0:
            raise ValueError("points must be a non-negative int")
        issue = self._jira.issue(key)
        current = getattr(issue.fields, 'customfield_10006', None)
        try:
            current_val = int(current) if current is not None else None
        except Exception:
            current_val = None
        if current_val == points:
            logger.debug("story points unchanged for %s (%s)", key, points)
            return
        logger.info("set story points for %s: %s", key, points)
        issue.update(fields={"customfield_10006": points})
