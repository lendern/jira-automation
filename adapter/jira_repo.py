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
    # Mutations are handled via update_fields
    # -----------------

    # -----------------
    # Generic field access
    # -----------------
    def get_fields(self, key: str, fields: List[str]) -> dict[str, Any]:
        fields_param = ",".join(sorted(set(fields))) if fields else None
        issue = self._jira.issue(key, fields=fields_param)
        out: dict[str, Any] = {}
        for f in fields or []:
            out[f] = getattr(issue.fields, f, None)
        return out

    def update_fields(self, key: str, fields: dict[str, Any]) -> None:
        # NOTE about field transforms (in_transform / out_transform):
        # - The logical field layer (lsd/fields.py) defines CustomFieldSpec with optional
        #   `in_transform` and `out_transform` to bridge Jira shapes <-> Python values.
        # - Callers typically use update_field(repo, issue_key, name, value[, merge]). That
        #   function applies `out_transform(value)` when present so that this method receives
        #   the final Jira payload (e.g., {"priority": {"name": "High"}} or
        #   {"customfield_16708": {"value": "UnitX"}}). Therefore, this method should not
        #   re-transform values; it only computes idempotent updates by comparing with current
        #   Jira state and sends the minimal diff.
        if not fields:
            return
        # Read current for idempotence
        cur = self.get_fields(key, list(fields.keys()))
        payload: dict[str, Any] = {}
        for k, v in fields.items():
            cv = cur.get(k)
            # List comparison (labels/components)
            if isinstance(v, list):
                # New names
                if v and isinstance(v[0], dict):
                    nv_names = sorted(set(str(d.get('name', '')) for d in v))
                else:
                    nv_names = sorted(set(str(x) for x in v))
                # Current names
                if isinstance(cv, list):
                    cv_names = sorted(set(str(getattr(x, 'name', x)) for x in cv))
                else:
                    cv_names = []
                if nv_names != cv_names:
                    payload[k] = v
                continue
            # Dict comparison for objects with 'name' (e.g., priority)
            if isinstance(v, dict) and 'name' in v:
                current_name = getattr(cv, 'name', None)
                if v.get('name') != current_name:
                    payload[k] = v
                continue
            # Fallback direct compare
            if v != cv:
                payload[k] = v

        if payload:
            logger.info("update fields for %s: %s", key, ", ".join(payload.keys()))
            issue = self._jira.issue(key)
            issue.update(fields=payload)
