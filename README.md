# jira-db

A set of scripts to take back control of your Jira data and help you manage it.

You can add your own cron jobs so that you can run the scripts at a specific time.

## Installation

```shell
git clone git@github.com:mcao2/jira-db.git --branch main
```

## Usage

### Create your `config.json`

You should create a JSON config file named `config.json` under current directory. 

It should contain the following keys:

```json
{
  "JiraServer": "<YOUR_VALUE>",
  "JiraProject": "<YOUR_VALUE>",
  "JiraAuthToken": "<YOUR_VALUE>",
  "DBRootDir": "<YOUR_VALUE>",
  "EmailSender": "<YOUR_VALUE>",
  "EmailPassword": "<YOUR_VALUE>",
  "EmailRecipient": "<YOUR_VALUE>",
  "EmailSMTPServer": "<YOUR_VALUE>",
  "EmailSMTPPort": "<YOUR_VALUE>"
}
```

### `python3 get_my_issues.py`

This will fetch all issues assigned to you and save them to the local `jira.db` database.

### `python3 generate_weekly_report.py`

This will generate a weekly report for the current week, save to the local `jira.db` database, and send an email to the configured recipient.
