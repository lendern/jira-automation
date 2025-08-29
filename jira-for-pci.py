"""
jira-for-pci.py

Command-line helper to operate on Jira issues for PCI-related automation.

This module:
- Parses CLI arguments (fiscal year, quarter, squad and operation flags).
- Validates year and quarter against supported values.
- Instantiates a JIRA client and an LSD helper (project-specific wrapper).
- Optionally triggers operations on the LSD object: propagate quarter label,
  propagate priorities, or find orphan LVL3 items.

Usage example:
    python jira-for-pci.py 26 1 Network --set-quarter

Note: This script expects JIRA_TOKEN in the environment.
"""
import os
import sys
import logging
from jira import JIRA
from lsd import LSD
import argparse

JIRA_SERVER = 'https://jira.ovhcloud.tools'
JIRA_TOKEN = os.getenv('JIRA_TOKEN')
if not JIRA_TOKEN:
    print('Missing required environment variable JIRA_TOKEN')
    sys.exit(1)
SUPPORTED_FY = ['26']
SUPPORTED_QUARTER = ['1', '2', '3', '4']

LVL2_to_exclude = []


def valid_year(s_year):
    """
    Validate the provided fiscal year.

    Args:
        s_year (str): Fiscal year string as provided on the CLI (e.g. '26').

    Side effects:
        Exits the process with code 0 after printing a message if the year
        is not in SUPPORTED_FY.

    Rationale:
        Keep validation strict and explicit to avoid accidental operations
        on unsupported fiscal years.
    """
    if s_year not in SUPPORTED_FY:
        print(f'Requested FY is {s_year}, expecting {SUPPORTED_FY}, exit')
        sys.exit(1)


def valid_quarter(s_quarter):
    """
    Validate the provided quarter.

    Args:
        s_quarter (str): Quarter string as provided on the CLI ('1'..'4').

    Side effects:
        Exits the process with code 0 after printing a message if the quarter
        is not in SUPPORTED_QUARTER.
    """
    if s_quarter not in SUPPORTED_QUARTER:
        print(f'Requested Quarter is {s_quarter}, expecting {SUPPORTED_QUARTER}, exit')
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="fiscal formated as '26'", type=str)
    parser.add_argument("quarter", help="quarter formated as '1'", type=str)
    parser.add_argument("squad", help="Squad to work on", type=str, choices=['Network'])
    parser.add_argument("--set-quarter", help="set quarter label in Epics and Tasks, based on LVL2", action='store_true')
    parser.add_argument("--set-prio", help="set quarter label in Epics and Tasks, based on LVL2", action='store_true')
    parser.add_argument("--find-orphans", help="find LVL3 which are not in tree of LSD in quarter", action='store_true')
    parser.add_argument("--dry-run", help="do not perform remote updates, only simulate", action='store_true')
    parser.add_argument("--verbose", help="enable verbose/debug logging", action='store_true')
    parser.add_argument("--update-estimate", help="sum story points of child stories/tasks and update PCI Epics", action='store_true')
    args = parser.parse_args()

    valid_year(args.year)
    valid_quarter(args.quarter)
    
    # logging configuration
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logger = logging.getLogger(__name__)

    try:
        jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_TOKEN)
    except Exception as e:
        logger.error('Failed to create JIRA client: %s', e)
        sys.exit(1)

    lsd = LSD(jira, args.year, args.quarter, args.squad, dry_run=args.dry_run)

    lsd.to_ascii()    
    if args.set_quarter:
        lsd.propagate_sprint()
    if args.set_prio:
        lsd.propagate_prio()
    if args.update_estimate:
        lsd.update_estimates()
    if args.find_orphans:
        lsd.find_orphans()

