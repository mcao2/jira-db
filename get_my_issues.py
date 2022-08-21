#!/usr/bin/env python3
# coding: utf-8

import json
from jira import JIRA

from util import find_all, simplify_author, get_current_date
from sqlite_helper import SQLiteHelper

## Load configs
with open('config.json', 'r') as f:
    configs = json.load(f)

## Setup jira client
jira_client = JIRA(configs.get('JiraServer'), token_auth=configs.get('JiraAuthToken'))

cur_user = jira_client.user(jira_client.current_user())
cur_timezone = cur_user.raw['timeZone']
print(f"Current user: {cur_user.name}, timezone: {cur_timezone}")

with SQLiteHelper(configs.get('DBRootDir')) as db:
    latest_ticket_date = db.get_latest_date("ticket", "createdDate", cur_timezone)
    if latest_ticket_date:
        print(f"Detected latest ticket as {latest_ticket_date} in {cur_timezone}")
    latest_retrival_date = db.get_latest_date("last_retrieval", "retrievalDate", cur_timezone)
    if latest_retrival_date:
        print(f"Detected latest retrieval as {latest_retrival_date} in {cur_timezone}")

    # Get all tickets after local latest ticket date
    search_cmd_str = "assignee = currentUser() "
    if latest_ticket_date:
        if latest_retrival_date:
            search_cmd_str += f" AND (createdDate > \"{latest_ticket_date}\" OR updatedDate > \"{latest_retrival_date}\")"

    all_new_issues = find_all(jira_client, search_cmd_str, simplify_raw=True)

    entries = []
    for issue in all_new_issues:
        # Extract comments
        # TODO: may need to consider pagination
        issue_comments = ""
        if "comment" in issue.raw['fields'] and "comments" in issue.raw['fields']['comment']:
            _comments = []
            for comment in issue.raw['fields']['comment']['comments']:
                _comments.append(simplify_author(comment))
            issue_comments = str(_comments)

        # Extract changelog
        # TODO: may need to consider pagination
        issue_changelog = ""
        if "changelog" in issue.raw['fields'] and "histories" in issue.raw['fields']['changelog']:
            _changelog = []
            for history in issue.raw['fields']['changelog']['histories']:
                _changelog.append(simplify_author(history))
            issue_changelog = str(_changelog)

        entries.append(
            (issue.key, issue.fields.reporter.name, issue.fields.assignee.name, issue.fields.description,
             issue.fields.status.name, issue_comments, issue_changelog, issue.fields.created, str(issue.raw)))

        db.add("ticket", entries)
        db.add("last_retrieval", [(get_current_date("UTC"), len(all_new_issues))])

    print("Updated database")
