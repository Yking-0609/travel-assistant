import sqlite3, os

class TravelDatabase:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), "travel.db")
        self.conn = None
        self._ensure_database()

    def _ensure_database(self):
        # Try to open and run a simple pragma; if it fails, delete file
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("PRAGMA integrity_check;")
                conn.close()
            except sqlite3.DatabaseError:
                print("⚠️ Malformed DB found – deleting and recreating …")
                try:
                    os.remove(self.db_path)
                except OSError:
                    pass

        # Always open a fresh connection after the check
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_query TEXT NOT NULL,
                    bot_reply TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"DB create_table error: {e}")
            self._reset_database()

    def save_search(self, user_query, bot_reply):
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO searches (user_query, bot_reply) VALUES (?, ?)",
                (user_query, bot_reply)
            )
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"DB write error: {e}")
            self._reset_database()

    def _reset_database(self):
        """Drop the file and rebuild from scratch."""
        try:
            self.conn.close()
        except Exception:
            pass
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_table()
        print("✅ Database recreated successfully.")
