# Setup & Configuration

Important environment variables
- JIRA_BASE_URL=https://your-domain.atlassian.net
- JIRA_API_TOKEN=xxxxxxxx
- JIRA_USER_EMAIL=you@domain.tld
- NODE_ENV=development|production
- DATABASE_URL=postgres://user:pass@host:port/db (if used)

Example .env file
Create a `.env` file in the project root:
```
JIRA_BASE_URL=https://...
JIRA_API_TOKEN=...
JIRA_USER_EMAIL=...
NODE_ENV=development
```

Docker (simple example)
- Build: docker build -t jira-automation .
- Run:
  docker run -e JIRA_API_TOKEN=... -e JIRA_BASE_URL=... jira-automation

Secrets and keys
- Store secrets in a vault or in CI secrets (GitHub Actions secrets, etc.)
- Do not commit `.env` or any secrets to the repository.

Database
- If the project uses a relational DB, run migrations before starting:
  - npm run migrate or the equivalent migration command for your stack.
- Ensure DATABASE_URL is set.

Tests
- Run unit tests: npm test or python -m pytest depending on project test setup.
- Integration tests may need real or mocked credentials.

Troubleshooting
- Check logs with npm run start or docker logs
- Authentication errors -> verify JIRA_API_TOKEN and JIRA_USER_EMAIL
- Rate limiting (429) -> implement retry/backoff
