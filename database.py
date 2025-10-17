import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


class TravelDatabase:
    def __init__(self):
        # Load PostgreSQL URL from environment
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("❌ DATABASE_URL not found in environment variables.")
        
        self.conn = None
        self._connect()

    def _connect(self):
        """(Re)connect to PostgreSQL database."""
        try:
            if self.conn:
                self.conn.close()
            self.conn = psycopg2.connect(self.db_url, sslmode="require")
            print("✅ Connected to PostgreSQL successfully!")
            self._create_table()
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.conn = None

    def _create_table(self):
        """Create the searches table if it doesn't already exist."""
        if not self.conn:
            print("⚠️ No active database connection to create table.")
            return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS searches (
                        id SERIAL PRIMARY KEY,
                        user_query TEXT NOT NULL,
                        bot_reply TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.conn.commit()
                print("✅ Table 'searches' ready.")
        except Exception as e:
            print(f"⚠️ Error creating table: {e}")
            self.conn.rollback()

    def save_search(self, user_query, bot_reply):
        """Insert a user query and bot reply, reconnect if needed."""
        if not self.conn:
            print("⚠️ No active DB connection — reconnecting …")
            self._connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO searches (user_query, bot_reply, created_at) VALUES (%s, %s, %s);",
                    (user_query, bot_reply, datetime.utcnow())
                )
                self.conn.commit()
                print("💾 Saved search successfully.")
        except psycopg2.InterfaceError:
            print("⚠️ Connection lost — attempting to reconnect …")
            self._connect()
            self.save_search(user_query, bot_reply)
        except Exception as e:
            print(f"⚠️ Error saving search: {e}")
            self.conn.rollback()

    def get_all_searches(self):
        """Fetch all searches from the database."""
        if not self.conn:
            print("⚠️ No active DB connection — reconnecting …")
            self._connect()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM searches ORDER BY created_at DESC;")
                return cur.fetchall()
        except psycopg2.InterfaceError:
            print("⚠️ Connection lost — reconnecting …")
            self._connect()
            return self.get_all_searches()
        except Exception as e:
            print(f"⚠️ Error reading searches: {e}")
            return []

    def __del__(self):
        """Close the DB connection cleanly."""
        try:
            if self.conn:
                self.conn.close()
                print("🔒 PostgreSQL connection closed.")
        except Exception:
            pass
