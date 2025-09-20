import logging
from typing import List

from adapter.ports import Repository
from nutree import Tree

from .mappers import to_domain
from .models import PCIssue, PCITaskStory, PCIEpic, IssueBase, LVL2Feature, LVL2Epic
from .labels import str_lvl3_sprint_label
from .fields import update_field, read_field


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
                update_field(repo, data.key, "labels", [label], merge=True)
            except Exception as e:
                logger.error('Failed to set label for %s: %s', data.key, e)


def propagate_priority(tree: Tree, repo: Repository) -> None:
    """Propagate Epic priority to related Tasks/Stories.

    - Direct children of each PCI Epic (via Epic Link) are updated.
    - Additionally, Tasks/Stories that share the same LVL2 Feature parent
      (siblings of the Epic under the feature) are also updated.
    """
    logger.info('Propagate priority from Epics to Tasks/Stories')
    for node in tree:
        data = node.data

        # Case 1: direct children of Epics
        if isinstance(data, PCIEpic):
            new_prio = data.prio
            logger.info('Epic %s priority is %s', data.key, new_prio)
            for child in node:
                c = child.data
                if isinstance(c, PCITaskStory) and not c.is_closed():
                    if c.prio != new_prio:
                        try:
                            update_field(repo, c.key, "priority", new_prio)
                            logger.info('(+) set prio %s for %s %s', new_prio, c.type, c.key)
                        except Exception as e:
                            logger.error('Failed to set priority for %s: %s', c.key, e)
                    else:
                        logger.debug('(-) unchanged prio for %s %s', c.type, c.key)

        # Case 2: siblings under the same LVL2 Feature
        if isinstance(data, LVL2Feature):
            # Find the Epic child (if any) to source the priority
            epic_prio = None
            for child in node:
                cd = child.data
                if isinstance(cd, PCIEpic):
                    epic_prio = cd.prio
                    break
            if epic_prio:
                for child in node:
                    cd = child.data
                    if isinstance(cd, PCITaskStory) and not cd.is_closed():
                        if cd.prio != epic_prio:
                            try:
                                update_field(repo, cd.key, "priority", epic_prio)
                                logger.info('(+) set prio %s for sibling %s %s', epic_prio, cd.type, cd.key)
                            except Exception as e:
                                logger.error('Failed to set priority for %s: %s', cd.key, e)


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
                update_field(repo, epic_key, "story_points", total)
                logger.info('(i) story points=%s for %s', total, epic_key)
            except Exception as e:
                logger.error('Failed to set story points for %s: %s', epic_key, e)
            return total
    raise KeyError(f'Epic {epic_key} not found in tree')


def update_lvl2_pu(tree: Tree, feature_key: str, value: str, repo: Repository) -> None:
    """Update the LVL2 Feature 'pu' field (customfield_16708) using the field abstraction.

    If the feature is present in the tree, logs its presence; otherwise still performs the update.
    """
    found = False
    for node in tree:
        d = node.data
        if isinstance(d, LVL2Feature) and d.key == feature_key:
            found = True
            break
    try:
        update_field(repo, feature_key, "pu", value)
        if found:
            logger.info("(i) Updated LVL2 Feature %s pu=%s", feature_key, value)
        else:
            logger.info("(i) Updated LVL2 Feature %s pu=%s (not in current tree)", feature_key, value)
    except Exception as e:
        logger.error("Failed to update 'pu' for %s: %s", feature_key, e)


def update_lvl2_blfnt(tree: Tree, epic_key: str, value: str, repo: Repository) -> None:
    """Update the LVL2 Epic 'blfnt' field (customfield_10530) using the field abstraction.

    If the epic is present in the tree, logs its presence; otherwise still performs the update.
    """
    found = False
    for node in tree:
        d = node.data
        if isinstance(d, LVL2Epic) and d.key == epic_key:
            found = True
            break
    try:
        update_field(repo, epic_key, "blfnt", value)
        if found:
            logger.info("(i) Updated LVL2 Epic %s blfnt=%s", epic_key, value)
        else:
            logger.info("(i) Updated LVL2 Epic %s blfnt=%s (not in current tree)", epic_key, value)
    except Exception as e:
        logger.error("Failed to update 'blfnt' for %s: %s", epic_key, e)


def read_issue_field(repo: Repository, issue_key: str, name: str):
    """Convenience wrapper to read a logical field using the abstraction.

    Example: read_issue_field(repo, 'LVL2-123', 'pu')
    """
    try:
        return read_field(repo, issue_key, name)
    except Exception as e:
        logger.error("Failed to read field '%s' for %s: %s", name, issue_key, e)
        raise


def update_issue_field(repo: Repository, issue_key: str, name: str, value, *, merge: bool = False) -> None:
    """Convenience wrapper to update a logical field using the abstraction.

    Example: update_issue_field(repo, 'PCI-123', 'labels', ['FY26Q2'], merge=True)
    """
    try:
        update_field(repo, issue_key, name, value, merge=merge)
    except Exception as e:
        logger.error("Failed to update field '%s' for %s: %s", name, issue_key, e)
        raise
