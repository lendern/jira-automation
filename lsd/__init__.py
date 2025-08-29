from nutree import Tree
from colorama import Fore, Style
from .lvl2 import LVL2feature, LVL2epic, str_lvl2_sprint_label
from .lvl3 import PCIEpic, PCITaskStory, str_lvl3_sprint_label

VALID_SPRINTS = ['SD-FY26-Q1', 'SD-FY26-Q2', 'SD-FY26-Q3', 'SD-FY26-Q4']

# ---------------------------------------------------------------------
# JQL query 
# ---------------------------------------------------------------------

JQL_LVL2_FOR_PCI_ROOT = ['project = LVL2', 'type = "New Feature"', 'Unit-Squad = PU.pCI']
JQL_PCI_ROOT = ['project = PCI', 'type in ("Epic", "Story", "Task")']

JQL_NOT_CLOSED = ['status NOT in (Done, Canceled, Cancelled, Closed)']

def _jql_build(s_root, l_filter_terms=[], b_not_closed = True):
    l_terms = s_root + l_filter_terms
    if b_not_closed:
        l_terms += JQL_NOT_CLOSED
    s_jql = ' AND '.join(l_terms) + ' ORDER BY priority DESC'
    print(f'Running SQL: "{s_jql}"')
    return s_jql

def _jql_query_lvl2_keys(jira, l_filter_terms=[]):
    issues = jira.search_issues(_jql_build(JQL_LVL2_FOR_PCI_ROOT, l_filter_terms), 
                                fields="key",
                                maxResults=False)
    return [issue.key for issue in issues]

def _jql_query_pci_keys_for_squas(jira, s_squad, l_filter_terms=[]):
    l_squad_filter = [f'Component = {s_squad}']
    issues = jira.search_issues(_jql_build(JQL_PCI_ROOT, l_filter_terms = l_squad_filter + l_filter_terms), 
                                fields="key",
                                maxResults=False)
    return [issue.key for issue in issues]

# ---------------------------------------------------------------------
# Issue management
# ---------------------------------------------------------------------

def issue_to_project_type(issue):
    project = issue.fields.project.key
    type = issue.fields.issuetype.name 
    return (project, type)   


def init_ovhissue(jira, issue, project: str, type: str):
    ovhissue = None
    if project == 'LVL2':
        if type == 'New Feature':
            ovhissue = LVL2feature(jira, issue)
        elif type == 'Epic LPM':
            ovhissue = LVL2epic(jira, issue)
    elif project == 'PCI':
        if type == 'Epic':
            ovhissue = PCIEpic(jira, issue)
        elif type in ('Story', 'Task'):
            ovhissue = PCITaskStory(jira, issue) 
    if not ovhissue:
        print(f'({project},{type}) is not supported, skip')
    return ovhissue


def reccursive_build_tree(jira, ancestor, key, s_squad):
    # 1. create Ovh Issue by key(type, summary, etc.)
    issue = jira.issue(key)
    proj, type = issue_to_project_type(issue)
    ovhissue = init_ovhissue(jira, issue, proj, type)
    if type == 'Epic':
        if s_squad == 'Network' and not ovhissue.is_network():
            return
    if ovhissue:
        # 2. node = ancestor.add(OvhIssue)
        node = ancestor.add(ovhissue)
        for childkey in ovhissue.childs:
            reccursive_build_tree(jira, node, childkey, s_squad)

def is_sprint_valid(s_sprint):
    if s_sprint not in VALID_SPRINTS:
        print(f'Expected sprint in *{VALID_SPRINTS}*, received *{s_sprint}*')
        return False
    else:
        return True


class LSD:
    PROJECT = 'LVL2'
    def __init__(self, jira, s_year, s_quarter, s_squad):
        self._jira = jira
        self.year = s_year
        self.quarter = s_quarter
        self.sprint = str_lvl2_sprint_label(s_year, s_quarter)
        self.s_squad = s_squad
        print('==============================================================================')
        print(f'Running LSD tree onto sprint = {self.sprint}')
        print('==============================================================================')
        self.tree = Tree(LSD.PROJECT)
        self.build_tree()

    def build_tree(self):
        l_filter_terms = [f'sprint = {self.sprint}']
        if self.s_squad == 'Network':
            l_filter_terms += [LVL2feature.JQL_NETWORK_ONLY]
        l_new_features = _jql_query_lvl2_keys(self._jira, l_filter_terms = l_filter_terms)
        for key in l_new_features:
            reccursive_build_tree(self._jira, self.tree, key, self.s_squad)

    def __str__(self):
        return self.tree.format()

    def to_ascii(self):
        print(self)
    
    def propagate_sprint(self):
        s_label = str_lvl3_sprint_label(self.year, self.quarter)
        print(f'Will know propagate label {s_label} to tree for {self.s_squad}')
        for node in self.tree:
            # Depth-first, pre-order by default
            ovhissue = node.data
            if ovhissue.project == 'PCI' :
                if ovhissue.type in ("Task", "Story", "Epic") and not ovhissue.is_closed():
                    ovhissue.add_label(s_label)

    def propagate_prio(self):
        print(f'Now, Will propagate priority, from Epics to Stories')
        # get all Epic keys
        for node in self.tree:
            ovhissue = node.data
            if ovhissue.project == 'PCI' and ovhissue.type == "Epic":
                # on cherche les Epics LVL3
                new_prio = ovhissue.prio
                print(f'prio *{new_prio}* for Epic *{str(ovhissue)}*')
                for task_or_story_node in node:
                    # on cherche les Epics LVL3
                    if not task_or_story_node.data.is_closed():
                        _issue = self._jira.issue(task_or_story_node.data.key)
                        if task_or_story_node.data.prio != new_prio:
                            _issue.update(fields={"priority": {"name": new_prio}})
                            print(f'(+) set prio *{new_prio}* for *{task_or_story_node.data.type}* *{str(task_or_story_node.data)}*')
                        else:
                            print(f'(-) unchanged prio for *{task_or_story_node.data.type}* *{str(task_or_story_node.data)}*')                        
        
    def find_orphans(self):
        # 1. find all LVL3 Issues that belongs to LSD
        l_issues_in_lsd = []
        for node in self.tree:
            ovhissue = node.data
            if ovhissue.project == 'PCI' and ovhissue.type in ("Task", "Story", "Epic"):
                l_issues_in_lsd.append(ovhissue.key)           
        
        # 2. find all LVL3 issues with appropriate quarter label
        label = str_lvl3_sprint_label(self.year, self.quarter)
        l_candidates_key = _jql_query_pci_keys_for_squas(self._jira, self.s_squad ,l_filter_terms=[f'labels = "{label}"'])
        for key in l_candidates_key:
            if key not in l_issues_in_lsd:
                issue = self._jira.issue(key)
                proj, type = issue_to_project_type(issue)
                ovhissue = init_ovhissue(self._jira, issue, proj, type)                
                print(f'(-) orphan {label} found: *{str(ovhissue)}*')                        


