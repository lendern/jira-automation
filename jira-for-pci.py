import os
import sys
import argparse
import logging
import re
from jira import JIRA
from lsd.logging_utils import setup_logging
from adapter import JiraRepository, SimRepository
from lsd.tree_builder import build_lsd_tree
from lsd.presenter import to_ascii
from lsd import services

JIRA_SERVER = 'https://jira.ovhcloud.tools'
JIRA_TOKEN = os.environ.get('JIRA_TOKEN')
SUPPORTED_FY = ['26']
SUPPORTED_QUARTER = ['1', '2', '3', '4']



logger = logging.getLogger(__name__)


def valid_year(s_year):
    if s_year not in SUPPORTED_FY:
        logger.error('Request FY is %s, expecting %s, exit', s_year, SUPPORTED_FY)
        sys.exit(1)

def valid_quarter(s_quarter):
    if s_quarter not in SUPPORTED_QUARTER:
        logger.error('Request Quarter is %s, expecting %s, exit', s_quarter, SUPPORTED_QUARTER)
        sys.exit(1)

def valid_pci_issue(s_pci_epic):
    if not re.search(r"^PCI-\d{4,5}$", s_pci_epic):
        logger.error('PCI Epic is %s, expecting PCI-xxxxx, exit', s_pci_epic)
        sys.exit(1)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="fiscal formated as '26'", type=str)
    parser.add_argument("quarter", help="quarter formated as '1'", type=str)
    parser.add_argument("squad", help="Squad to work on", type=str, choices=['Network'])
    parser.add_argument("--action", help="...", type=str, choices=["set-quarter", "set-prio", "find-orphans", "aggregate-points"])
    parser.add_argument("--update", help="Apply updates to Jira (default is simulation)", action='store_true')
    parser.add_argument("--skip-closed", help="skip and LVL3 closed (only compatible with view)", action='store_true')
    parser.add_argument("--pci-epic", help="PCI epics to apply dedicated action", type=str)
    args = parser.parse_args()

    # Configure logging: fixed handlers
    # - Console level: INFO
    # - File level: DEBUG at ./out/logs.txt
    setup_logging(log_file='./out/logs.txt')
    logger.debug("CLI parsed args: %s", args)

    # Validate environment
    if not JIRA_TOKEN:
        logger.error('Environment variable JIRA_TOKEN is required but missing')
        sys.exit(1)
    if not JIRA_SERVER:
        logger.error('Environment variable JIRA_SERVER is empty')
        sys.exit(1)

    valid_year(args.year)
    valid_quarter(args.quarter)
    
    # default: build tree and print
    jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_TOKEN)
    base_repo = JiraRepository(jira)
    if args.update:
        repo = base_repo
        logger.info('Update mode enabled: changes will be applied to Jira')
    else:
        repo = SimRepository(base_repo)
        logger.info('Simulation mode (default): no changes will be applied. Use --update to apply.')
    tree = build_lsd_tree(repo, args.year, args.quarter, args.squad, args.skip_closed)
    print(to_ascii(tree))

    # actions tweak
    if args.skip_closed:
        logger.warning('--skip-closed flag is set, skipping any other commands')
    elif args.action:
        if args.action == "set-quarter":
            services.propagate_sprint(tree, args.year, args.quarter, repo)
        elif args.action == "set-prio":
            services.propagate_priority(tree, repo)
        elif args.action == "find-orphans":
            services.find_orphans(tree, args.year, args.quarter, args.squad, repo)
        elif args.action == "aggregate-points":
            if args.pci_epic:
                valid_pci_issue(args.pci_epic)
                services.aggregate_points(tree, args.pci_epic, repo)
            else:
                logger.error('--pci-epic is MD with --actions=aggregate-points, exit')
                sys.exit(1)
    else:
        logger.info('No action defined, exit')
