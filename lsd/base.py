"""
lsd.base

Base wrappers for Jira issue objects used by the LSD tooling.

Contains a lightweight OvhIssue wrapper that exposes frequently used fields
and helper methods to interact with the underlying jira-python issue object.
"""

import logging

logger = logging.getLogger(__name__)


class OvhIssue:
    """
    Generic wrapper around a Jira issue used by the LSD tooling.

    This wrapper keeps a reference to the Jira client and the underlying
    jira issue object. It extracts frequently used fields into attributes
    and provides convenience methods (for example to add labels).

    Attributes:
        _jira: Jira client instance used for API operations.
        _issue: Underlying jira-python issue object.
        childs (list): Child issue keys or OvhIssue instances.
        id: placeholder id attribute.
        key (str): Jira issue key.
        project (str): Project key of the issue.
        type (str): Issue type name.
        title (str): Issue summary.
        labels (list): Current labels on the issue.
        status (str): Current status name.
        prio (str): Priority name.
    """
    # Common to all types (Epics, Story, etc)
    def __init__(self, jira, issue=None, key=None, dry_run=False):
        """
        Initialize the OvhIssue wrapper.

        Args:
            jira: Authenticated Jira client instance.
            issue: Optional jira-python Issue object. If provided, used directly.
            key: Optional issue key string. If provided and `issue` is None, the
                 issue is fetched from Jira.
        """
        self._jira = jira
        if issue:
            self._issue = issue
        elif key:
            self._issue = jira.issue(key)
        self.childs = []
        # honor dry-run mode to avoid remote updates
        self.dry_run = dry_run

        # primary fields
        # store the underlying issue id (not the builtin id)
        self.id = getattr(self._issue, 'id', None)
        self.key = self._issue.key

        # secondary fields
        _fields = self._issue.fields
        self.project = _fields.project.key
        self.type = _fields.issuetype.name
        self.title = _fields.summary
        self.labels = _fields.labels
        self.status = _fields.status.name
        self.prio = _fields.priority.name


    def __str__(self):
        """
        Return a compact human-readable representation.

        Returns:
            str: "KEY | Type | Status | Title" string.
        """
        return ' | '.join([self.key, self.type, self.status, self.title])

    def __repr__(self):
        """
        Return a debug-friendly representation (delegates to __str__).
        """
        return self.__str__()
    
    def add_label(self, s_new_label):
        """
        Add a label to the Jira issue if not already present and persist it.

        Args:
            s_new_label (str): Label to add.

        Side effects:
            - Updates the remote issue via the Jira client when a new label is added.
            - Prints a short message indicating whether the label was added or skipped.
        """
        if s_new_label not in self.labels:
            logger.info('(+) add label *%s* to *%s*', s_new_label, str(self))
            self.labels.append(s_new_label)
            if self.dry_run:
                logger.info('[dry-run] would update labels for %s: %s', self.key, self.labels)
                return
            # update the already-fetched underlying issue object when possible
            try:
                self._issue.update(fields={"labels": self.labels})
            except Exception:
                # fallback to refetching the issue if the stored object cannot be updated
                _issue = self._jira.issue(self.key)
                _issue.update(fields={"labels": self.labels})
        else:
            logger.debug('(-) skip, label *%s* already in *%s*', s_new_label, str(self))
