import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

class TravelDatabase:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")

        if not self.db_url:
            raise ValueError("❌ DATABASE_URL not found in environment variables.")

        self.conn = psycopg2.connect(self.db_url, sslmode="require")
        self._create_table()

    def _create_table(self):
        """Create searches table if it doesn't exist"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS searches (
                    id SERIAL PRIMARY KEY,
                    user_input TEXT NOT NULL,
                    bot_reply TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()

    def save_search(self, user_input, bot_reply):
        """Insert a chat record"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO searches (user_input, bot_reply, timestamp)
                VALUES (%s, %s, %s);
            """, (user_input, bot_reply, datetime.utcnow()))
            self.conn.commit()

    def get_all_searches(self):
        """Retrieve all saved chats"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM searches ORDER BY timestamp DESC;")
            return cursor.fetchall()

    def __del__(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
