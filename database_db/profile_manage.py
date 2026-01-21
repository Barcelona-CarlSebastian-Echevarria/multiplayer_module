import sqlite3
import uuid
import os
from datetime import datetime

DB_FILE = "profiles.db"

class ProfileManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        # Create table if not exists
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_profile (
                local_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                best_survival_record INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        self.conn.commit()

    # ---------- PROFILE CREATION ----------
    def create_profile(self, name: str):
        local_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        best_survival_record = 0  # Initialize field

        self.cursor.execute("""
            INSERT INTO player_profile 
            (local_id, name, created_at, best_survival_record)
            VALUES (?, ?, ?, ?)
        """, (local_id, name, created_at, best_survival_record))

        self.conn.commit()
        return local_id

    # ---------- LOAD PROFILE ----------
    def load_profile(self):
        self.cursor.execute("""
            SELECT local_id, name, games_played, wins, losses, best_survival_record
            FROM player_profile
            LIMIT 1
        """)
        row = self.cursor.fetchone()
        return row

    # ---------- UPDATE STATS ----------
    def update_stats(self, win=False, loss=False, survival_time=None):
        profile = self.load_profile()
        if not profile:
            return

        local_id = profile[0]
        games_played = profile[2] + 1
        wins = profile[3] + (1 if win else 0)
        losses = profile[4] + (1 if loss else 0)
        best_survival_record = profile[5]

        # Update best survival record if new survival_time is higher
        if survival_time is not None and survival_time > best_survival_record:
            best_survival_record = survival_time

        self.cursor.execute("""
            UPDATE player_profile
            SET games_played=?, wins=?, losses=?, best_survival_record=?
            WHERE local_id=?
        """, (games_played, wins, losses, best_survival_record, local_id))

        self.conn.commit()
