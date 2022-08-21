import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List


class SQLiteHelper:
    """
    Local SQLite DB helper
    """
    DB_NAME = "jira.db"

    def __init__(self, root_dir):
        root_dir_path = Path(root_dir)
        root_dir_path.mkdir(exist_ok=True)
        self.db_path = root_dir_path / self.DB_NAME
        self.db_conn = sqlite3.connect(str(self.db_path))
        self.db_cursor = None

    def __enter__(self):
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute("PRAGMA journal_mode=WAL;")
        self.db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS ticket(key TEXT PRIMARY KEY, reporter TEXT NOT NULL, assignee TEXT NOT NULL, description TEXT, status TEXT NOT NULL, comment TEXT, changelog TEXT, createdDate TEXT NOT NULL, raw TEXT NOT NULL);"
        )
        self.db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS last_retrieval(retrievalDate TEXT PRIMARY KEY, retrievalCount INTEGER NOT NULL);"
        )
        self.db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS weekly_report(week_start TEXT PRIMARY KEY, resolved TEXT NOT NULL, testing TEXT NOT NULL, in_progress TEXT NOT NULL, open TEXT NOT NULL, updatedDate TEXT NOT NULL);"
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Save (commit) the changes
        self.db_conn.commit()
        self.db_conn.close()

    def add(self, table_name: str, entries: List):
        """
        Add one or more entries to the db.
        Args:
            table_name (str): table name that we add data to.
            entries (List): a list of tuples containing required data.
        """
        assert self.db_cursor is not None, "DB cursor is not initialized"
        # Check if all entries have same number of fields
        num_fields = set()
        for entry in entries:
            num_fields.add(len(entry))
        if len(num_fields) == 0:
            return
        elif len(num_fields) > 1:
            raise RuntimeError(
                f"Inconsistent number of fields provided for insertion to table {table_name}: {num_fields}")

        cmd_str = f"REPLACE INTO {table_name} VALUES ({','.join(['?'] * num_fields.pop())})"

        self.db_cursor.executemany(cmd_str, entries)

    def get_latest_date(self, table_name, col_name, target_tz):
        """
        Get latest date we have
        """
        assert self.db_cursor is not None, "DB cursor is not initialized"
        latest_date = None
        rows = self.db_cursor.execute(f"SELECT max({col_name}) from {table_name};").fetchone()
        if rows[0] is not None:
            latest_date = datetime.strptime(rows[0], "%Y-%m-%dT%H:%M:%S.%f%z")
            # Convert to target timezone
            latest_date = latest_date.astimezone(ZoneInfo(target_tz)).strftime("%Y-%m-%d %H:%M")
        return latest_date
