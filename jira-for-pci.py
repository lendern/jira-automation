import os
from jira import JIRA
from lsd import LSD
import argparse

JIRA_SERVER = 'https://jira.ovhcloud.tools'
JIRA_TOKEN = os.environ['JIRA_TOKEN']
SUPPORTED_FY = ['26']
SUPPORTED_QUARTER = ['1', '2', '3', '4']

LVL2_to_exclude = []


def valid_year(s_year):
    if s_year not in SUPPORTED_FY:
        print(f'Requested FY is {s_year}, expecting {SUPPORTED_FY}, exit')
        exit(0)

def valid_quarter(s_quarter):
    if s_quarter not in SUPPORTED_QUARTER:
        print(f'Requested Quarter is {s_quarter}, expecting {SUPPORTED_QUARTER}, exit')
        exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="fiscal formated as '26'", type=str)
    parser.add_argument("quarter", help="quarter formated as '1'", type=str)
    parser.add_argument("squad", help="Squad to work on", type=str, choices=['Network'])
    parser.add_argument("--set-quarter", help="set quarter label in Epics and Tasks, based on LVL2", action='store_true')
    parser.add_argument("--set-prio", help="set quarter label in Epics and Tasks, based on LVL2", action='store_true')
    parser.add_argument("--find-orphans", help="find LVL3 which are not in tree of LSD in quarter", action='store_true')
    args = parser.parse_args()

    valid_year(args.year)
    valid_quarter(args.quarter)
    
    jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_TOKEN)
    lsd = LSD(jira, args.year, args.quarter, args.squad)

    lsd.to_ascii()    
    if args.set_quarter:
        lsd.propagate_sprint()
    if args.set_prio:
        lsd.propagate_prio()
    if args.find_orphans:
        lsd.find_orphans()

