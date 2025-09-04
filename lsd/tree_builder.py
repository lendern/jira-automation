import logging
from typing import Callable

from nutree import Tree

from adapter.ports import Repository
from .mappers import to_domain
from .models import PCIEpic, PCIssue
from .lvl2 import str_lvl2_sprint_label


logger = logging.getLogger(__name__)


def _child_keys_for(issue, repo: Repository, squad: str):
    """Return next-level child keys for the given domain issue.

    Mirrors the current behavior:
    - LVL2 New Feature -> PCI children by Parent Link (Epic/Story/Task filtered to Network)
    - PCI Epic -> Stories/Tasks by Epic Link (filtered to Network)
    - Others -> no children
    """
    if issue.project == 'LVL2' and issue.type == 'New Feature':
        return repo.find_pci_children_by_parent_link(issue.key)
    if issue.project == 'PCI' and issue.type == 'Epic':
        return repo.find_children_by_epic_link(issue.key, squad)
    return []


def _recurse_add(repo: Repository, ancestor, key: str, squad: str, skip_closed: bool):
    # Load raw issue and map to domain
    raw = repo.get_issue(key)
    dom = to_domain(raw)

    # Filter: for Network squad, drop PCI Epics not in Network
    if isinstance(dom, PCIEpic) and squad == 'Network' and not dom.is_network():
        logger.debug('skip non-network Epic %s', dom.key)
        return

    # Filter: optionally skip closed PCI issues
    if isinstance(dom, PCIssue) and skip_closed and dom.is_closed():
        logger.debug('skip closed PCI issue %s', dom.key)
        return

    node = ancestor.add(dom)
    for child_key in _child_keys_for(dom, repo, squad):
        _recurse_add(repo, node, child_key, squad, skip_closed)


def build_lsd_tree(repo: Repository, year: str, quarter: str, squad: str, skip_closed: bool) -> Tree:
    """Build and return the LSD tree using the repository (no direct Jira calls).

    Root items are LVL2 New Features in the sprint SD-FY{year}-Q{quarter},
    filtered for the given squad when applicable.
    """
    sprint = str_lvl2_sprint_label(year, quarter)
    logger.info('Build LSD tree for sprint %s (squad=%s, skip_closed=%s)', sprint, squad, skip_closed)
    tree = Tree('LVL2')
    for key in repo.find_lvl2_new_features(sprint, squad):
        _recurse_add(repo, tree, key, squad, skip_closed)
    return tree

