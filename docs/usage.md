# Usage — Quick Guide

Common commands
- Development:
  - npm run dev (if applicable)
  - python jira-for-pci.py 26 1 Network --set-quarter
- Build & start:
  - npm run build
  - npm start

Testing
- Unit tests:
  - npm test or python -m pytest
- Integration tests:
  - npm run test:integration (may require real credentials or mocks)

CLI examples (Python helper)
- List rules (example CLI wrapper):
  - npm run cli -- list-rules
- Execute a rule manually:
  - npm run cli -- run-rule --name="rule_name"

Webhooks
- Expected endpoint: POST /webhook
- Minimal payload: see tests in /tests or the integration specs

Best practices
- Keep rules small and unit-testable.
- Mock Jira calls in CI to avoid hitting real APIs.

Common troubleshooting
- 401 / 403: verify token and user email
- 429: handle rate limits using backoff and retries
- 5xx Jira: implement retry and alerting
