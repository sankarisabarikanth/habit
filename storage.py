import sqlite3
import threading
import os
import sys

class SQLStorage:
    """
    A thread-safe SQLite-backed data store for habits and journals.
    Conforms to the original InMemoryStorage interface to ensure compatibility.
    """
    def __init__(self):
        # Detect if we are running under a testing framework
        is_testing = (
            "unittest" in sys.modules or 
            "pytest" in sys.modules or 
            os.environ.get("FLASK_ENV") == "testing" or 
            os.environ.get("TESTING") == "true"
        )
        self.db_path = "habits_test.db" if is_testing else "habits.db"
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                # 1. Habits table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS habits (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        created_at TEXT,
                        streak_current INTEGER DEFAULT 0,
                        streak_longest INTEGER DEFAULT 0,
                        completion_percentage REAL DEFAULT 0.0
                    )
                """)
                # 2. Completions table (one-to-many relationship)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS completions (
                        habit_id TEXT,
                        completion_date TEXT,
                        PRIMARY KEY (habit_id, completion_date),
                        FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
                    )
                """)
                # 3. Journals table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journals (
                        id TEXT PRIMARY KEY,
                        date TEXT UNIQUE,
                        title TEXT,
                        content TEXT,
                        mood TEXT,
                        created_at TEXT
                    )
                """)
                # 4. Journal Habits table (many-to-many relationship)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_habits (
                        journal_id TEXT,
                        habit_id TEXT,
                        PRIMARY KEY (journal_id, habit_id),
                        FOREIGN KEY (journal_id) REFERENCES journals(id) ON DELETE CASCADE,
                        FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def get_all(self):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM habits")
                rows = cursor.fetchall()
                habits = [dict(row) for row in rows]
                
                # Fetch completions for each habit
                for h in habits:
                    cursor.execute("SELECT completion_date FROM completions WHERE habit_id = ?", (h["id"],))
                    comp_rows = cursor.fetchall()
                    h["completions"] = [row["completion_date"] for row in comp_rows]
                return habits
            finally:
                conn.close()

    def get_by_id(self, habit_id):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                habit = dict(row)
                cursor.execute("SELECT completion_date FROM completions WHERE habit_id = ?", (habit_id,))
                comp_rows = cursor.fetchall()
                habit["completions"] = [r["completion_date"] for r in comp_rows]
                return habit
            finally:
                conn.close()

    def save(self, habit):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                # Upsert the habit details
                cursor.execute("""
                    INSERT INTO habits (id, name, description, category, created_at, streak_current, streak_longest, completion_percentage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        description=excluded.description,
                        category=excluded.category,
                        created_at=excluded.created_at,
                        streak_current=excluded.streak_current,
                        streak_longest=excluded.streak_longest,
                        completion_percentage=excluded.completion_percentage
                """, (
                    habit["id"],
                    habit["name"],
                    habit.get("description", ""),
                    habit.get("category", "Other"),
                    habit["created_at"],
                    habit.get("streak_current", 0),
                    habit.get("streak_longest", 0),
                    habit.get("completion_percentage", 0.0)
                ))
                
                # Update completions (delete and re-insert to keep list accurate)
                cursor.execute("DELETE FROM completions WHERE habit_id = ?", (habit["id"],))
                for comp in habit.get("completions", []):
                    cursor.execute("INSERT INTO completions (habit_id, completion_date) VALUES (?, ?)", (habit["id"], comp))
                
                conn.commit()
                return dict(habit)
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def delete(self, habit_id):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
                success = cursor.rowcount > 0
                conn.commit()
                return success
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def get_all_journals(self):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM journals")
                rows = cursor.fetchall()
                journals = [dict(row) for row in rows]
                
                # Fetch linked habit ids for each journal
                for j in journals:
                    cursor.execute("SELECT habit_id FROM journal_habits WHERE journal_id = ?", (j["id"],))
                    habit_rows = cursor.fetchall()
                    j["habit_ids"] = [row["habit_id"] for row in habit_rows]
                return journals
            finally:
                conn.close()

    def get_journal_by_id(self, journal_id):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM journals WHERE id = ?", (journal_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                journal = dict(row)
                cursor.execute("SELECT habit_id FROM journal_habits WHERE journal_id = ?", (journal_id,))
                habit_rows = cursor.fetchall()
                journal["habit_ids"] = [r["habit_id"] for r in habit_rows]
                return journal
            finally:
                conn.close()

    def save_journal(self, journal):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                # Upsert the journal details
                cursor.execute("""
                    INSERT INTO journals (id, date, title, content, mood, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        date=excluded.date,
                        title=excluded.title,
                        content=excluded.content,
                        mood=excluded.mood,
                        created_at=excluded.created_at
                """, (
                    journal["id"],
                    journal["date"],
                    journal.get("title", ""),
                    journal.get("content", ""),
                    journal.get("mood", "Neutral"),
                    journal.get("created_at", "")
                ))
                
                # Update journal habits links
                cursor.execute("DELETE FROM journal_habits WHERE journal_id = ?", (journal["id"],))
                for hid in journal.get("habit_ids", []):
                    cursor.execute("INSERT INTO journal_habits (journal_id, habit_id) VALUES (?, ?)", (journal["id"], hid))
                
                conn.commit()
                return dict(journal)
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def delete_journal(self, journal_id):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM journals WHERE id = ?", (journal_id,))
                success = cursor.rowcount > 0
                conn.commit()
                return success
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def clear(self):
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                # Cascades will automatically clean up completions and journal_habits
                cursor.execute("DELETE FROM habits")
                cursor.execute("DELETE FROM journals")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

# Global storage instance
db = SQLStorage()
