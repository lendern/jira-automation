"""
lsd package initializer

Provides high-level helpers to query Jira with JQL, instantiate OvhIssue
wrappers and build an in-memory tree representing LVL2 -> LVL3 relationships.
"""
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
    """
    Build a JQL string from a root list and optional filters.

    Args:
        s_root (list): Base JQL clauses.
        l_filter_terms (list): Additional filter clauses to append.
        b_not_closed (bool): When True, append a NOT closed filter.

    Returns:
        str: Full JQL string with ORDER BY priority DESC.
    """
    l_terms = s_root + l_filter_terms
    if b_not_closed:
        l_terms += JQL_NOT_CLOSED
    s_jql = ' AND '.join(l_terms) + ' ORDER BY priority DESC'
    print(f'Running SQL: "{s_jql}"')
    return s_jql

def _jql_query_lvl2_keys(jira, l_filter_terms=[]):
    """Return keys of LVL2 New Feature issues matching the built JQL."""
    issues = jira.search_issues(_jql_build(JQL_LVL2_FOR_PCI_ROOT, l_filter_terms), 
                                fields="key",
                                maxResults=False)
    return [issue.key for issue in issues]

def _jql_query_pci_keys_for_squas(jira, s_squad, l_filter_terms=[]):
    """Return PCI issue keys for a given squad and optional filters."""
    l_squad_filter = [f'Component = {s_squad}']
    issues = jira.search_issues(_jql_build(JQL_PCI_ROOT, l_filter_terms = l_squad_filter + l_filter_terms), 
                                fields="key",
                                maxResults=False)
    return [issue.key for issue in issues]

# ---------------------------------------------------------------------
# Issue management
# ---------------------------------------------------------------------

def issue_to_project_type(issue):
    """
    Extract (project, type) tuple from a jira Issue object.

    Args:
        issue: jira-python Issue object.

    Returns:
        tuple: (project_key, issue_type_name)
    """
    project = issue.fields.project.key
    type = issue.fields.issuetype.name 
    return (project, type)   


def init_ovhissue(jira, issue, project: str, type: str):
    """
    Instantiate the appropriate OvhIssue subclass for a given project/type.

    Returns:
        OvhIssue or None: Initialized wrapper or None if unsupported.
    """
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
    """
    Recursively build the in-memory tree of OvhIssue wrappers.

    Args:
        jira: Jira client
        ancestor: nutree node to attach children to
        key: issue key to initialize and traverse
        s_squad: squad name used to filter certain Epics
    """
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
    """
    Validate that a sprint label is known/allowed.

    Returns:
        bool: True when sprint is in VALID_SPRINTS.
    """
    if s_sprint not in VALID_SPRINTS:
        print(f'Expected sprint in *{VALID_SPRINTS}*, received *{s_sprint}*')
        return False
    else:
        return True


class LSD:
    """
    Top-level orchestrator that builds an LVL2->LVL3 tree for a given sprint.

    The LSD instance holds the Jira client, target year/quarter, squad and the
    in-memory tree representation (nutree.Tree).
    """
    PROJECT = 'LVL2'
    def __init__(self, jira, s_year, s_quarter, s_squad):
        """
        Create and populate the LSD tree for the requested sprint.

        Args:
            jira: Jira client instance.
            s_year (str): Fiscal year (e.g. '26').
            s_quarter (str): Quarter number (e.g. '1').
            s_squad (str): Squad name (e.g. 'Network').
        """
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
        """
        Query LVL2 New Features for the configured sprint and build the tree.
        """
        l_filter_terms = [f'sprint = {self.sprint}']
        if self.s_squad == 'Network':
            l_filter_terms += [LVL2feature.JQL_NETWORK_ONLY]
        l_new_features = _jql_query_lvl2_keys(self._jira, l_filter_terms = l_filter_terms)
        for key in l_new_features:
            reccursive_build_tree(self._jira, self.tree, key, self.s_squad)

    def __str__(self):
        """Return the formatted tree as string."""
        return self.tree.format()

    def to_ascii(self):
        """Print the formatted tree to stdout."""
        print(self)
    
    def propagate_sprint(self):
        """
        Propagate the LVL3 sprint/quarter label from LSD context to LVL3 issues.

        Only non-closed PCI issues of supported types will be labeled.
        """
        s_label = str_lvl3_sprint_label(self.year, self.quarter)
        print(f'Will know propagate label {s_label} to tree for {self.s_squad}')
        for node in self.tree:
            # Depth-first, pre-order by default
            ovhissue = node.data
            if ovhissue.project == 'PCI' :
                if ovhissue.type in ("Task", "Story", "Epic") and not ovhissue.is_closed():
                    ovhissue.add_label(s_label)

    def propagate_prio(self):
        """
        Propagate priority from Epics to their direct child stories/tasks.

        For each PCI Epic in the tree, set the same priority on non-closed child issues.
        """
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
        """
        Find LVL3 issues labeled for the target quarter that are not present in the LSD tree.

        Prints out discovered orphan issues.
        """
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


