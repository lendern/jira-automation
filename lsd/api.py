"""
lsd.api

Thin wrapper around a jira client to centralize calls, error handling
and simple retries. This is intentionally minimal at first: it provides
search/get/update convenience methods that other modules can use.
"""
import logging
import time

logger = logging.getLogger(__name__)


class JiraAPI:
    def __init__(self, jira_client, retry_on_exception=True, retries=2, backoff=1.0):
        self._jira = jira_client
        self.retry_on_exception = retry_on_exception
        self.retries = retries
        self.backoff = backoff

    def search(self, jql, fields=None, max_results=False):
        """Return list of Issue objects from jira.search_issues.

        Args:
            jql (str): JQL query string.
            fields (str|list): fields to request.
            max_results (bool|int): False or integer.
        """
        attempt = 0
        while True:
            try:
                issues = self._jira.search_issues(jql, fields=fields, maxResults=max_results)
                return list(issues)
            except Exception as e:
                attempt += 1
                logger.exception('Jira search failed (attempt %s): %s', attempt, e)
                if not self.retry_on_exception or attempt > self.retries:
                    raise
                time.sleep(self.backoff * attempt)

    def get(self, key):
        try:
            return self._jira.issue(key)
        except Exception:
            logger.exception('Failed to fetch issue %s', key)
            raise

    def update(self, key, fields):
        try:
            issue = self._jira.issue(key)
            issue.update(fields=fields)
        except Exception:
            logger.exception('Failed to update issue %s with %s', key, fields)
            raise
