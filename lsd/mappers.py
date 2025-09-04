import logging
from typing import Any, Optional

from .models import (
    IssueBase,
    LVL2Epic,
    LVL2Feature,
    PCIEpic,
    PCITaskStory,
    PCIssue,
)


logger = logging.getLogger(__name__)


def _safe_priority_name(fields: Any) -> Optional[str]:
    prio = getattr(fields, "priority", None)
    return getattr(prio, "name", None)


def _safe_labels(fields: Any) -> list[str]:
    labels = getattr(fields, "labels", None) or []
    return list(labels)


def _safe_components(fields: Any) -> list[str]:
    comps = getattr(fields, "components", None) or []
    return [getattr(c, "name", "") for c in comps]


def _safe_story_points(fields: Any) -> int:
    sp = getattr(fields, "customfield_10006", None)
    try:
        return int(sp) if sp is not None else 0
    except Exception:
        return 0


def to_domain(issue: Any) -> IssueBase | PCIssue:
    """Map a jira.Issue-like object to a pure domain model instance.

    Note: This function only reads fields from the given issue object and
    does not perform any network calls.
    """
    fields = issue.fields
    project = getattr(fields.project, "key", "")
    itype = getattr(fields.issuetype, "name", "")
    title = getattr(fields, "summary", "")
    status = getattr(fields.status, "name", "")
    prio_name = _safe_priority_name(fields)
    labels = _safe_labels(fields)

    if project == "LVL2":
        if itype == "Epic LPM":
            blfnt = getattr(fields, "customfield_10530", None)
            blfnt_val = getattr(blfnt, "value", "na") if blfnt else "na"
            return LVL2Epic(
                key=issue.key,
                project=project,
                type=itype,
                title=title,
                status=status,
                labels=labels,
                prio=prio_name,
                blfnt=blfnt_val,
            )
        elif itype == "New Feature":
            pu = getattr(fields, "customfield_16708", None)
            pu_val = getattr(pu, "value", "na") if pu else "na"
            return LVL2Feature(
                key=issue.key,
                project=project,
                type=itype,
                title=title,
                status=status,
                labels=labels,
                prio=prio_name,
                pu=pu_val,
            )

    if project == "PCI":
        comps = _safe_components(fields)
        sp = _safe_story_points(fields)
        if itype == "Epic":
            return PCIEpic(
                key=issue.key,
                project=project,
                type=itype,
                title=title,
                status=status,
                labels=labels,
                prio=prio_name,
                components=comps,
                story_points=sp,
            )
        if itype in ("Story", "Task"):
            return PCITaskStory(
                key=issue.key,
                project=project,
                type=itype,
                title=title,
                status=status,
                labels=labels,
                prio=prio_name,
                components=comps,
                story_points=sp,
            )

    logger.warning("Unsupported issue type mapping: (%s, %s) for %s", project, itype, issue.key)
    return IssueBase(
        key=issue.key,
        project=project,
        type=itype,
        title=title,
        status=status,
        labels=labels,
        prio=prio_name,
    )

