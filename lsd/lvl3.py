"""
lsd.lvl3

Helpers and lightweight wrappers for LVL3 (PCI) Jira issues.

Provides:
- utility functions for sprint label formatting
- PCIEpic and PCITaskStory wrappers extending OvhIssue with LVL3-specific logic
"""
from colorama import Fore, Style
import logging
from lsd.base import OvhIssue

logger = logging.getLogger(__name__)

def str_strike(s_string):
    """Return a string wrapped with ANSI strike-through codes."""
    return '\033[9m'+s_string+'\033[0m'

def str_lvl3_sprint_label(s_year, s_quarter):
    """Return the LVL3-style sprint/quarter label (e.g. 'FY26Q1')."""
    return f'FY{s_year}Q{s_quarter}'

# ======================================================================
# LVL3 issues
# ======================================================================

class PCIEpic(OvhIssue):
    """
    Wrapper for PCI Epics.

    Extends OvhIssue with methods to fetch components, child items and
    small helpers used by LSD flows.
    """
    def __init__(self, jira, issue=None, key=None):
        """
        Initialize a PCIEpic and populate fields and childs list.

        Args:
            jira: Jira client instance.
            key: Issue key of the Epic.
        """
        OvhIssue.__init__(self, jira, issue=issue, key=key)
        assert self.type == 'Epic'
        self.get_fields()
        self.get_childs()

    def __str__(self):
        """
        Provide a colored string representation; strike-through when closed.
        """
        string = OvhIssue.__str__(self)
        string = Fore.BLUE + string + Style.RESET_ALL
        if self.is_closed():
            return str_strike(string)
        else:
            return string

    def get_fields(self):
        """
        Read and populate Epic-specific fields (for now: components).
        """
        _fields = self._issue.fields
        # Get Components
        self.components = [component.name for component in _fields.components]
        pass

    def get_childs(self):
        """
        Populate self.childs with keys of issues linked to this Epic restricted to Network component.
        """
        issues = self._jira.search_issues(f'"Epic Link" = {self.key} AND \
                            type in (Epic, Story, Task) AND \
                            Component = "Network" \
                            ORDER by status', maxResults=False)
        self.childs =  [issue.key for issue in issues]

    def set_org_estimate(self, i_estimate):
        """Placeholder to set an organization estimate on the Epic (no-op)."""
        pass
    
    def is_network(self):
        """Return True if the Epic has the 'Network' component."""
        return 'Network' in self.components

    def is_closed(self):
        """Return True if the Epic is in a terminal/closed status."""
        return self.status in ("Done", "To Prod", "Cancelled", "Canceled")


class PCITaskStory(OvhIssue):
    """
    Wrapper for PCI Tasks and Stories.

    Adds access to the (custom) estimate field and a display string.
    """
    def __init__(self, jira, issue=None, key=None):
        """
        Initialize a task/story and set its estimate (customfield_10006).
        """
        OvhIssue.__init__(self, jira, issue=issue, key=key)
        assert self.type in ['Task' , 'Story']
        _fields = self._issue.fields
        if _fields.customfield_10006:
            self.estimate = int(_fields.customfield_10006)
        else:
            self.estimate = 0

    def __str__(self):
        """
        Return a formatted single-line string including estimate and status.
        """
        string = ' | '.join([
            self.key, 
            self.type, 
            str(self.estimate).rjust(2, ' '), 
            self.status.ljust(13, ' '), 
            self.title])
        if self.is_closed():
            return str_strike(string)
        else:
            return string

    def is_closed(self):
        """Return True when the issue status is considered closed/terminal."""
        return self.status in ("Done", "To Prod", "Cancelled", "Canceled")


