import logging


logger = logging.getLogger(__name__)


class OvhIssue:
    # Common to all types (Epics, Story, etc)
    def __init__(self, jira, issue=None, key=None):
        self._jira = jira
        if issue:
            self._issue = issue
        elif key:
            self._issue = jira.issue(key)
        self.childs = []

        # primary fields
        self.id = id
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
        return ' | '.join([self.key, self.type, self.status, self.title])

    def __repr__(self):
        return self.__str__()
    
    def add_label(self, s_new_label):
        if s_new_label not in self.labels:
            logger.info('(+) add label %s to %s', s_new_label, str(self))
            self.labels.append(s_new_label)
            _issue = self._jira.issue(self.key)
            _issue.update(fields={"labels": self.labels})
        else:
            logger.debug('(-) skip, label %s already present on %s', s_new_label, str(self))

