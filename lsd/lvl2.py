import logging
from colorama import Fore, Style
from lsd.base import OvhIssue

def str_lvl2_sprint_label(s_year, s_quarter):
    return f'SD-FY{s_year}-Q{s_quarter}'

# ======================================================================
# LVL2 issues
# ======================================================================

class LVL2feature(OvhIssue):
    JQL_NETWORK_PRODUCT_ONLY = '"OVH Product" in ("Public cloud Network - Floating IP (Neutron)", "Public cloud Network - Load Balancer (Octavia)", "Public cloud Network - Public & Private Network (Neutron)", "Public cloud Network - Public Gateway (Neutron)")'
    JQL_NETWORK_CONTRIB_ONLY = '"Contributor(s) Squad(s) (Manual)" = "PU.pCI/Network"'
    JQL_NETWORK_ONLY = f'(({JQL_NETWORK_PRODUCT_ONLY}) OR ({JQL_NETWORK_CONTRIB_ONLY}))'
    
    def __init__(self, jira, key):
        OvhIssue.__init__(self, jira, key=key)
        assert self.type == 'New Feature'
        self.get_fields()
        self.get_childs()
    
    def get_fields(self):
        _fields = self._issue.fields
        # Unit
        if _fields.customfield_16708:
            self.pu = _fields.customfield_16708.value
        else:
            self.pu = 'na'
 
    def get_childs(self):
        issues = self._jira.search_issues(f'Project = PCI AND \
                                    "Parent Link" = {self.key} AND \
                                    type in (Epic, Story, Task) AND \
                                    (Component = "Network" OR labels = "Openstack_Networking")', maxResults=False)
        self.childs = [issue.key for issue in issues]

    def __str__(self):
        string = ' | '.join([self.key.ljust(10, ' '), 
                           self.prio.ljust(10, ' '), 
                           self.status.ljust(12, ' '),
                           self.pu, 
                           self.title])
        return (Fore.YELLOW + string + Style.RESET_ALL)
    
    def __repr__(self):
        return self.__str__()


class LVL2epic(OvhIssue):
    def __init__(self, jira, key):
        OvhIssue.__init__(self, jira, key=key)
        assert self.type == 'Epic LPM'
        self.get_fields()
        self.get_childs()
    
    def get_fields(self):
        pass
        _fields = self._issue.fields

        # BNFNT
        if _fields.customfield_10530:
            self.blfnt = _fields.customfield_10530.value
        else:
            self.blfnt = 'na'
 
    def get_childs(self):
        issues = self._jira.search_issues(f'Project = LVL2 AND \
                                    type = "New Feature" AND \
                                    "Parent Link" = {self.key}', maxResults=False)
        self.childs = [issue.key for issue in issues]


    def __str__(self):
        string = ' | '.join([self.key.ljust(10, ' '), 
                           self.status.ljust(12, ' '),
                           self.blfnt, 
                           self.title])
        return (Fore.GREEN + string + Style.RESET_ALL)
    
    def __repr__(self):
        return self.__str__()
