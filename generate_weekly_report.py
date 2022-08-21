#!/usr/bin/env python3
# coding: utf-8

import json
import smtplib, ssl
from jira import JIRA
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from util import find_all, get_current_date
from sqlite_helper import SQLiteHelper

## Load configs
with open('config.json', 'r') as f:
    configs = json.load(f)

## Setup jira client
jira_client = JIRA(configs.get('JiraServer'), token_auth=configs.get('JiraAuthToken'))

cur_user = jira_client.user(jira_client.current_user())
cur_timezone = cur_user.raw['timeZone']
print(f"Current user: {cur_user.name}, timezone: {cur_timezone}")

## Fetch data from jira
search_cmd_str = f"project = {configs.get('JiraProject')} AND assignee = currentUser() AND sprint IN openSprints()"
all_sprint_issues = find_all(jira_client, search_cmd_str, simplify_raw=True)

today = datetime.now(ZoneInfo(cur_timezone)).date()
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=6)
print(f"Week start: {week_start}, week end: {week_end}")

all_resolved_this_week = []  # tickets changed to resolved this week
all_testing_this_week = []  # tickets changed to testing or have any update this week
all_in_progress_this_week = []  # tickets that I am working on and not resolved this week
all_open_this_week = []  # tickets left open or newly added this week

for issue in all_sprint_issues:
    issue_detail = {
        'key':
            issue.key,
        'status':
            issue.fields.status.name,
        'summary':
            issue.fields.summary,
        'reporter':
            issue.fields.reporter.name,
        'createdDate':
            datetime.strptime(issue.fields.created, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(ZoneInfo(cur_timezone)),
        'updatedDate':
            datetime.strptime(issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(ZoneInfo(cur_timezone)),
    }
    if issue.fields.status.statusCategory.name.lower() == "done":
        # Filter out tickets that were resolved last week
        resolution_date = datetime.strptime(issue.fields.resolutiondate,
                                            "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(ZoneInfo(cur_timezone)).date()
        if resolution_date >= week_start and resolution_date <= week_end:
            all_resolved_this_week.append(issue_detail)
    elif issue.fields.status.name.lower() == "testing":
        update_date = datetime.strptime(issue.fields.updated,
                                        "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(ZoneInfo(cur_timezone)).date()
        if update_date >= week_start and update_date <= week_end:
            all_testing_this_week.append(issue_detail)
    elif issue.fields.status.name.lower() == "in progress":
        all_in_progress_this_week.append(issue_detail)
    else:
        all_open_this_week.append(issue_detail)


## Sorting
def get_issue_id(cur_issue):
    return int(cur_issue['key'].split('-')[1])


all_resolved_this_week.sort(key=get_issue_id)
all_testing_this_week.sort(key=get_issue_id)
all_in_progress_this_week.sort(key=get_issue_id)
all_open_this_week.sort(key=get_issue_id)

## Save to database
with SQLiteHelper(configs.get('DBRootDir')) as db:
    db.add("weekly_report", [(week_start, str(all_resolved_this_week), str(all_testing_this_week),
                              str(all_in_progress_this_week), str(all_open_this_week), get_current_date("UTC"))])
    print("Saved to database")


## Email
def compose_issue_detail(issue_details, section_title):
    cnt = 1
    msg = f"{section_title}: {len(issue_details)} issues\n"
    for issue in issue_details:
        msg += f"{cnt}. {issue['key']} - {issue['status']} - {issue['summary']}\n"
        cnt += 1
    return msg


message = f"""\
From: {configs.get('EmailSender')}
To: {configs.get('EmailRecipient')}
Subject: Weekly Jira Report {week_start} - {week_end}

Hi {cur_user.name},

Here is your weekly report:

{compose_issue_detail(all_resolved_this_week, "Resolved this week")}

{compose_issue_detail(all_testing_this_week, "Testing this week")}

{compose_issue_detail(all_in_progress_this_week, "In progress this week")}

{compose_issue_detail(all_open_this_week, "Open this week")}

Best,
"""

# Create a secure SSL context
context = ssl.create_default_context()
with smtplib.SMTP(configs.get('EmailSMTPServer'), configs.get('EmailSMTPPort')) as server:
    server.ehlo()  # Can be omitted
    server.starttls(context=context)
    server.ehlo()  # Can be omitted
    server.login(configs.get('EmailSender'), configs.get('EmailPassword'))
    server.sendmail(configs.get('EmailSender'), configs.get('EmailRecipient'), message)
    print(f"Email sent to {configs.get('EmailRecipient')}")
