# jira-automation

Overview
- Automation tooling for Jira: scripts, webhooks and integrations to automate
  creation, transition and assignment of issues based on rules.

Key features
- Rule evaluation engine for automations
- Jira REST API integration via a small client/wrapper
- Executable via CLI, webhooks, or scheduler

Prerequisites
- Node.js 16+ (if Node parts exist) or Python 3.8+ for Python scripts
- Docker (optional)
- Jira API credentials (API token or OAuth depending on setup)

Quick install (local)
1. git clone <repo>
2. cd jira-automation
3. Install dependencies (project may contain both Node and Python components):
   - npm install (if applicable)
   - pip install -r requirements.txt (if Python components are used)
4. Configure environment variables (see docs/setup.md)

Start (examples)
- Development:
  - npm run dev or python jira-for-pci.py (see usage)
- Production:
  - npm run build && npm start
- Docker: see docs/setup.md for an example

Examples
- Run the Python helper:
  - python jira-for-pci.py 26 1 Network --set-quarter

Useful links
- docs/architecture.md — architecture and components
- docs/setup.md — configuration and secrets
- docs/usage.md — usage guide and troubleshooting
- CONTRIBUTING.md — how to contribute

License
- Indicate project license here (e.g. MIT) or check LICENSE file.
