
from colorama import Fore, Style
from lsd.base import OvhIssue

def str_strike(s_string):
    return '\033[9m'+s_string+'\033[0m'

def str_lvl3_sprint_label(s_year, s_quarter):
    return f'FY{s_year}Q{s_quarter}'

# ======================================================================
# LVL3 issues
# ======================================================================

class PCIEpic(OvhIssue):
    def __init__(self, jira, key):
        OvhIssue.__init__(self, jira, key=key)
        assert self.type == 'Epic'
        self.get_fields()
        self.get_childs()

    def __str__(self):
        string = OvhIssue.__str__(self)
        string = Fore.BLUE + string + Style.RESET_ALL
        if self.is_closed():
            return str_strike(string)
        else:
            return string

    def get_fields(self):
        _fields = self._issue.fields
        # Get Components
        self.components = [component.name for component in _fields.components]
        pass

    def get_childs(self):
        issues = self._jira.search_issues(f'"Epic Link" = {self.key} AND \
                            type in (Epic, Story, Task) AND \
                            Component = "Network" \
                            ORDER by status', maxResults=False)
        self.childs =  [issue.key for issue in issues]

    def set_org_estimate(self, i_estimate):
    
        pass
    
    def is_network(self):
        return 'Network' in self.components

    def is_closed(self):
        return self.status in ("Done", "To Prod", "Cancelled", "Canceled")


class PCITaskStory(OvhIssue):
    def __init__(self, jira, key):
        OvhIssue.__init__(self, jira, key=key)
        assert self.type in ['Task' , 'Story']
        _fields = self._issue.fields
        if _fields.customfield_10006:
            self.estimate = int(_fields.customfield_10006)
        else:
            self.estimate = 0

    def __str__(self):
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
        return self.status in ("Done", "To Prod", "Cancelled", "Canceled")
    

        