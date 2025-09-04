import logging
from typing import List

from adapter.ports import Repository
from nutree import Tree

from .mappers import to_domain
from .models import PCIssue, PCITaskStory, PCIEpic, IssueBase
from .lvl3 import str_lvl3_sprint_label


logger = logging.getLogger(__name__)


def propagate_sprint(tree: Tree, year: str, quarter: str, repo: Repository) -> None:
    """Add the FY{year}Q{quarter} label to all non-closed PCI issues in the tree.

    Writes via repository only; does not mutate domain objects in-memory.
    """
    label = str_lvl3_sprint_label(year, quarter)
    logger.info('Propagate sprint label %s to PCI issues', label)
    for node in tree:
        data = node.data
        if isinstance(data, PCIssue) and not data.is_closed() and data.type in ("Task", "Story", "Epic"):
            try:
                # Fetch current labels from repo to avoid duplicates based on stale state
                raw = repo.get_issue(data.key)
                cur = list(getattr(raw.fields, 'labels', []) or [])
                if label not in cur:
                    cur.append(label)
                repo.set_labels(data.key, cur)
            except Exception as e:
                logger.error('Failed to set label for %s: %s', data.key, e)


def propagate_priority(tree: Tree, repo: Repository) -> None:
    """Propagate priority from PCI Epics down to their direct Stories/Tasks."""
    logger.info('Propagate priority from Epics to Tasks/Stories')
    for node in tree:
        data = node.data
        if isinstance(data, PCIEpic):
            new_prio = data.prio
            logger.info('Epic %s priority is %s', data.key, new_prio)
            for child in node:
                c = child.data
                if isinstance(c, PCITaskStory) and not c.is_closed():
                    if c.prio != new_prio:
                        try:
                            repo.set_priority(c.key, new_prio)
                            logger.info('(+) set prio %s for %s %s', new_prio, c.type, c.key)
                        except Exception as e:
                            logger.error('Failed to set priority for %s: %s', c.key, e)
                    else:
                        logger.debug('(-) unchanged prio for %s %s', c.type, c.key)


def find_orphans(tree: Tree, year: str, quarter: str, squad: str, repo: Repository) -> List[IssueBase]:
    """Return PCI issues labeled for the quarter but not present in LSD tree.

    Also logs each orphan for visibility.
    """
    label = str_lvl3_sprint_label(year, quarter)
    in_tree = set()
    for node in tree:
        d = node.data
        if isinstance(d, PCIssue) and d.type in ("Task", "Story", "Epic"):
            in_tree.add(d.key)

    orphans: List[IssueBase] = []
    for key in repo.find_pci_keys_with_label_and_squad(label, squad):
        if key not in in_tree:
            raw = repo.get_issue(key)
            dom = to_domain(raw)
            orphans.append(dom)
            logger.warning('(-) orphan %s found: %s', label, str(dom))
    return orphans


def aggregate_points(tree: Tree, epic_key: str, repo: Repository) -> int:
    """Sum story points of an Epic's direct children and update the Epic.

    Returns the computed total. Raises KeyError if the epic is not in the tree.
    """
    target: PCIEpic | None = None
    for node in tree:
        d = node.data
        if isinstance(d, PCIEpic) and d.key == epic_key:
            target = d
            # Compute only direct children as in current logic
            total = 0
            for child in node:
                cd = child.data
                if isinstance(cd, PCIssue):
                    total += int(cd.story_points or 0)
            try:
                repo.set_story_points(epic_key, total)
                logger.info('(i) story points=%s for %s', total, epic_key)
            except Exception as e:
                logger.error('Failed to set story points for %s: %s', epic_key, e)
            return total
    raise KeyError(f'Epic {epic_key} not found in tree')

