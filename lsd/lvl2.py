"""
lsd.lvl2

Helpers and wrappers for LVL2 Jira issues (New Feature, Epic LPM).

Includes sprint label formatting and LVL2-specific field extraction.
"""
from colorama import Fore, Style
from lsd.base import OvhIssue

def str_lvl2_sprint_label(s_year, s_quarter):
    """Return the LVL2 sprint label (e.g. 'SD-FY26-Q1')."""
    return f'SD-FY{s_year}-Q{s_quarter}'

# ======================================================================
# LVL2 issues
# ======================================================================

class LVL2feature(OvhIssue):
    """
    Wrapper for LVL2 New Feature issues.

    Extracts LVL2-specific fields such as PU and can collect child LVL3 keys.
    """
    JQL_NETWORK_PRODUCT_ONLY = '"OVH Product" in ("Public cloud Network - Floating IP (Neutron)", "Public cloud Network - Load Balancer (Octavia)", "Public cloud Network - Public & Private Network (Neutron)", "Public cloud Network - Public Gateway (Neutron)")'
    JQL_NETWORK_CONTRIB_ONLY = '"Contributor(s) Squad(s) (Manual)" = "PU.pCI/Network"'
    JQL_NETWORK_ONLY = f'(({JQL_NETWORK_PRODUCT_ONLY}) OR ({JQL_NETWORK_CONTRIB_ONLY}))'
    
    def __init__(self, jira, key):
        """
        Initialize a LVL2feature and populate fields and children.

        Args:
            jira: Jira client instance.
            key: Issue key of the LVL2 New Feature.
        """
        OvhIssue.__init__(self, jira, key=key)
        assert self.type == 'New Feature'
        self.get_fields()
        self.get_childs()
    
    def get_fields(self):
        """
        Populate LVL2-specific fields (e.g. customfield_16708 -> pu).
        """
        _fields = self._issue.fields
        # Unit
        if _fields.customfield_16708:
            self.pu = _fields.customfield_16708.value
        else:
            self.pu = 'na'
 
    def get_childs(self):
        """
        Populate self.childs with keys of LVL3 issues linked under this New Feature.
        """
        issues = self._jira.search_issues(f'Project = PCI AND \
                                    "Parent Link" = {self.key} AND \
                                    type in (Epic, Story, Task) AND \
                                    (Component = "Network" OR labels = "Openstack_Networking")', maxResults=False)
        self.childs = [issue.key for issue in issues]

    def __str__(self):
        """
        Return a colored, single-line representation of the LVL2 feature.
        """
        string = ' | '.join([self.key.ljust(10, ' '), 
                           self.prio.ljust(10, ' '), 
                           self.status.ljust(12, ' '),
                           self.pu, 
                           self.title])
        return (Fore.YELLOW + string + Style.RESET_ALL)
    
    def __repr__(self):
        """Delegate to __str__ for convenience."""
        return self.__str__()


class LVL2epic(OvhIssue):
    """
    Wrapper for LVL2 Epic LPM issues.

    Extracts Epic-specific LVL2 fields and lists child New Features.
    """
    def __init__(self, jira, key):
        """
        Initialize LVL2epic and populate fields and children.
        """
        OvhIssue.__init__(self, jira, key=key)
        assert self.type == 'Epic LPM'
        self.get_fields()
        self.get_childs()
    
    def get_fields(self):
        """Populate LVL2 epic specific fields (example: customfield_10530 -> blfnt)."""
        pass
        _fields = self._issue.fields

        # BNFNT
        if _fields.customfield_10530:
            self.blfnt = _fields.customfield_10530.value
        else:
            self.blfnt = 'na'
 
    def get_childs(self):
        """Populate self.childs with New Feature keys that belong to this LVL2 epic."""
        issues = self._jira.search_issues(f'Project = LVL2 AND \
                                    type = "New Feature" AND \
                                    "Parent Link" = {self.key}', maxResults=False)
        self.childs = [issue.key for issue in issues]


    def __str__(self):
        """Return a colored one-line representation of the LVL2 epic."""
        string = ' | '.join([self.key.ljust(10, ' '), 
                           self.status.ljust(12, ' '),
                           self.blfnt, 
                           self.title])
        return (Fore.GREEN + string + Style.RESET_ALL)
    
    def __repr__(self):
        """Delegate to __str__."""
        return self.__str__()
