import json
import os
import sqlite3
from typing import List

from algohealer.db.enums import CATEGORIES, Settings


class SQLiteManager:
    def __init__(self, drop: bool = False):
        self.db_path = os.getenv("ALGOHEALER_DB_PATH", f"{os.getcwd()}/algohealer.db")
        self.connection = None
        self.cursor = None
        self._connect()
        if drop:
            self.drop_tables()
        self.initialize_tables()

    def _connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def close(self):
        if self.connection:
            self.connection.close()

    def initialize_tables(self):
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            site TEXT NOT NULL,
            category TEXT NOT NULL
        )
        """
        )
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL
        )
        """
        )
        self.connection.commit()

    def add_default_accounts(self):
        path = os.getenv(
            "ALGOHEALER_DEFAULT_ACCOUNTS_PATH",
            f"{os.getcwd()}/default_accounts.json",
        )
        if os.path.exists(path):
            with open(path, "r") as f:
                default_accounts = json.load(f)
            for account in default_accounts.get("accounts", []):
                self.add_account(**account)

    def drop_tables(self):
        self.cursor.execute("DROP TABLE IF EXISTS accounts")
        self.cursor.execute("DROP TABLE IF EXISTS settings")
        self.connection.commit()

    def check_settings_exist(self) -> bool:
        self.cursor.execute("SELECT name FROM settings")
        return len(self.cursor.fetchall()) > 0

    def get_settings(self) -> Settings:
        self.cursor.execute("SELECT name, value FROM settings")
        results = self.cursor.fetchall()
        settings = {}
        for result in results:
            # Convert to boolean
            if result[1] in ["0", "1"]:
                settings[result[0]] = result[1] == "1"
            if result[0] == "interests":
                settings[result[0]] = json.loads(result[1])
            else:
                settings[result[0]] = result[1]
        return Settings(**settings)

    def upsert_settings(self, settings: Settings):
        for key, value in settings.dict().items():
            if key == "interests":
                value = json.dumps(value)

            self.cursor.execute(
                "INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)",
                (key, value),
            )
        self.connection.commit()

    def add_account(self, name: str, site: str, category: str) -> int:
        if category not in CATEGORIES:
            raise ValueError(f"Category must be one of {CATEGORIES}")
        self.cursor.execute(
            "INSERT INTO accounts (name, site, category) VALUES (?, ?, ?)",
            (name, site, category),
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def delete_accounts(self, account_ids: List[int]):
        for account_id in account_ids:
            self.cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.connection.commit()

    def get_all_accounts_for_site(self, site: str) -> List[dict]:
        eligible_interests = json.loads(
            self.cursor.execute(
                "SELECT value FROM settings WHERE name = 'interests'"
            ).fetchone()[0]
        )
        interests = ", ".join([f"'{interest}'" for interest in eligible_interests])
        self.cursor.execute(
            f"""SELECT * FROM accounts WHERE
            site = ? AND category IN ({interests})""",
            (site,),
        )

        results = self.cursor.fetchall()
        return [
            {
                "id": result[0],
                "name": result[1],
                "site": result[2],
                "category": result[3],
            }
            for result in results
        ]
