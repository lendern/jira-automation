import os
import argparse
import logging
import re
from jira import JIRA
from lsd import LSD
from lsd.logging_utils import setup_logging

JIRA_SERVER = 'https://jira.ovhcloud.tools'
JIRA_TOKEN = os.environ['JIRA_TOKEN']
SUPPORTED_FY = ['26']
SUPPORTED_QUARTER = ['1', '2', '3', '4']

LVL2_to_exclude = []


logger = logging.getLogger(__name__)


def valid_year(s_year):
    if s_year not in SUPPORTED_FY:
        logger.error('Request FY is %s, expecting %s, exit', s_year, SUPPORTED_FY)
        exit(0)

def valid_quarter(s_quarter):
    if s_quarter not in SUPPORTED_QUARTER:
        logger.error('Request Quarter is %s, expecting %s, exit', s_quarter, SUPPORTED_QUARTER)
        exit(0)

def valid_pci_issue(s_pci_epic):
    if not re.search(r"^PCI-\d{4,5}$", s_pci_epic):
        logger.error('PCI Epic is %s, expecting PCI-xxxxx, exit', s_pci_epic)
        exit(0)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="fiscal formated as '26'", type=str)
    parser.add_argument("quarter", help="quarter formated as '1'", type=str)
    parser.add_argument("squad", help="Squad to work on", type=str, choices=['Network'])
    parser.add_argument("--action", help="...", type=str, choices=["set-quarter", "set-prio", "find-orphans", "aggregate-points"])
    parser.add_argument("--skip-closed", help="skip and LVL3 closed (only compatible with view)", action='store_true')
    parser.add_argument("--pci-epic", help="PCI epics to apply dedicated action", type=str)
    args = parser.parse_args()

    # Configure logging: fixed handlers
    # - Console level: INFO
    # - File level: DEBUG at ./out/logs.txt
    setup_logging(log_file='./out/logs.txt')
    logger.debug("CLI parsed args: %s", args)

    valid_year(args.year)
    valid_quarter(args.quarter)
    
    # default: build tree and print
    jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_TOKEN)
    lsd = LSD(jira, args.year, args.quarter, args.squad, args.skip_closed)
    lsd.to_ascii()

    # actions tweak
    if args.skip_closed:
        logger.warning('--skip-closed flag is set, skipping any other commands')
    elif args.action:
        if args.action == "set-quarter":
            lsd.propagate_sprint()
        elif args.action == "set-prio":
            lsd.propagate_prio()
        elif args.action == "find-orphans":
            lsd.find_orphans()
        elif args.action == "aggregate-points":
            if args.pci_epic:
                valid_pci_issue(args.pci_epic)
                lsd.aggregate_points(args.pci_epic)
            else:
                logger.error('--pci-epic is MD with --actions=aggregate-points, exit')
                exit(0)
    else:
        logger.info('No action defined, exit')
