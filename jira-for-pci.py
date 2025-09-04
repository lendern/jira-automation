import os
from jira import JIRA
from lsd import LSD
import argparse
import re

JIRA_SERVER = 'https://jira.ovhcloud.tools'
JIRA_TOKEN = os.environ['JIRA_TOKEN']
SUPPORTED_FY = ['26']
SUPPORTED_QUARTER = ['1', '2', '3', '4']

LVL2_to_exclude = []


def valid_year(s_year):
    if s_year not in SUPPORTED_FY:
        print(f'Request FY is {s_year}, expecting {SUPPORTED_FY}, exit')
        exit(0)

def valid_quarter(s_quarter):
    if s_quarter not in SUPPORTED_QUARTER:
        print(f'Request Quarter is {s_quarter}, expecting {SUPPORTED_QUARTER}, exit')
        exit(0)

def valid_pci_issue(s_pci_epic):
    if not re.search(r"^PCI-\d{4,5}$", s_pci_epic):
        print(f'PCI Epic is {s_pci_epic}, expecting PCI-xxxxx, exit')
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

    valid_year(args.year)
    valid_quarter(args.quarter)
    
    # default: build tree and print
    jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_TOKEN)
    lsd = LSD(jira, args.year, args.quarter, args.squad, args.skip_closed)
    lsd.to_ascii()

    # actions tweak
    if args.skip_closed:
        print('(w) --skip-closed flag is set, skipping any other commands')
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
                print(f'--pci-epic is MD with --actions=aggregate-points, exit')
                exit(0)
    else:
        print('No action defined, exit')                

