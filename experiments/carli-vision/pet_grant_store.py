"""P0-A Build5: offline SQLite pet grants; deny by default.

Demo-only administrative mutation interface. A real service must restrict
who can mutate grants and use a trusted identity provider.
"""
import sqlite3
from pathlib import Path

class PetGrantStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS pet_grants (
                owner_id TEXT NOT NULL, pet_id TEXT NOT NULL, scope TEXT NOT NULL,
                active INTEGER NOT NULL CHECK(active IN (0,1)),
                PRIMARY KEY(owner_id,pet_id,scope))""")

    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def set_grant_for_test(self, owner_id, pet_id, scope, active):
        """Only test harnesses may administer grants; NEVER expose to a client."""
        if not all(isinstance(v, str) and v for v in (owner_id, pet_id, scope)):
            raise ValueError("invalid grant")
        if type(active) is not bool:
            raise ValueError("active must be boolean")
        with self._db() as db:
            db.execute("""INSERT INTO pet_grants VALUES(?,?,?,?)
                ON CONFLICT(owner_id,pet_id,scope)
                DO UPDATE SET active=excluded.active""",
                (owner_id, pet_id, scope, int(active)))

    def check(self, owner_id, pet_id, scope):
        if not all(isinstance(v, str) and v for v in (owner_id, pet_id, scope)):
            return False
        try:
            with self._db() as db:
                row = db.execute("""SELECT active FROM pet_grants
                    WHERE owner_id=? AND pet_id=? AND scope=?""",
                    (owner_id, pet_id, scope)).fetchone()
        except sqlite3.Error:
            return False
        return row is not None and row[0] == 1
