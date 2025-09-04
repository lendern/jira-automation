
import logging
from colorama import Fore, Style
from lsd.base import OvhIssue

def str_strike(s_string):
    return '\033[9m'+s_string+'\033[0m'

def str_lvl3_sprint_label(s_year, s_quarter):
    return f'FY{s_year}Q{s_quarter}'

# ======================================================================
# LVL3 issues
# ======================================================================

class PCIissue(OvhIssue):
    def __init__(self, jira, key=None):
        OvhIssue.__init__(self, jira, key=key)
        _fields = self._issue.fields

        # component(s)
        self.components = [component.name for component in _fields.components]

        # story points
        if _fields.customfield_10006:
            self.story_points = int(_fields.customfield_10006)
        else:
            self.story_points = 0

    def __str__(self):
        string = ' | '.join([
            self.key, 
            self.type, 
            str(self.story_points).rjust(3, ' '), 
            self.status.ljust(13, ' '), 
            self.title])
        if self.is_closed():
            return str_strike(string)
        else:
            return string

    def is_closed(self):
        return self.status in ("Done", "To Prod", "Cancelled", "Canceled")

    def set_story_points(self, i_sp):
        if not isinstance(i_sp, int):
            logging.getLogger(__name__).error('expecting int for story points, exit')
            exit(0)
        if i_sp < 0:
            logging.getLogger(__name__).error('story points >= 0, exit')
            exit(0)
        # Dont modify if issue is closed
        if self.is_closed():
            logging.getLogger(__name__).info('(i) story points unchanged for %s', str(self))
        else:
            self._issue.update(fields={"customfield_10006": i_sp})
            self.story_points = i_sp
            logging.getLogger(__name__).info('(i) story points=%s for %s', i_sp, str(self))


class PCIEpic(PCIissue):
    def __init__(self, jira, key):
        PCIissue.__init__(self, jira, key=key)
        assert self.type == 'Epic'
        self.get_childs()

    def __str__(self):
        string = PCIissue.__str__(self)
        string = Fore.BLUE + string + Style.RESET_ALL
        return string

    def get_fields(self):
        _fields = self._issue.fields
        # Get Components
        self.components = [component.name for component in _fields.components]

    def get_childs(self):
        issues = self._jira.search_issues(f'"Epic Link" = {self.key} AND \
                            type in (Epic, Story, Task) AND \
                            Component = "Network" \
                            ORDER by status', maxResults=False)
        self.childs =  [issue.key for issue in issues]
    
    def is_network(self):
        return 'Network' in self.components

    def is_closed(self):
        return self.status in ("Done", "To Prod", "Cancelled", "Canceled")


class PCITaskStory(PCIissue):
    def __init__(self, jira, key):
        PCIissue.__init__(self, jira, key=key)
        assert self.type in ['Task' , 'Story']
